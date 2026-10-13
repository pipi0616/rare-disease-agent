"""The HTTP layer, through FastAPI's test client and the typed client: in process, on the
miniature HPO release with a scripted model."""

import json
import logging
import threading
from collections.abc import Callable
from typing import Any

import mlflow
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult

from conftest import ScriptedModel, answer, call
from raredx.agent import Agent
from raredx.data.cases import Case
from raredx.knowledge.hpo import HPO
from raredx.service import examples
from raredx.service.app import create_app
from raredx.service.client import Client, ServiceError
from raredx.service.diagnoser import Diagnoser
from raredx.service.schemas import DiagnoseRequest, DiagnoseResponse, Step
from raredx.tools.find_similar_patients import FindSimilarPatients
from raredx.tools.rank_candidate_genes import RankCandidateGenes

SNHL, AMENORRHEA = "HP:0000407", "HP:0000786"
BODY = {"hpo_ids": [SNHL, AMENORRHEA]}
FITS = ("OMIM:690001", "Hearing-ovarian syndrome", "explains both findings")

Served = Callable[..., TestClient]


@pytest.fixture
def served(hpo: HPO, patients: list[Case]) -> Served:
    """The service over a scripted model (or none), as a test client."""

    def build(model: Any = None, **options: Any) -> TestClient:
        agent = with_genes = None
        if model is not None:
            bank = FindSimilarPatients(hpo, patients, "test bank")
            tools = [bank, RankCandidateGenes(hpo)]
            agent = Agent(model, "fake-model", hpo, seeded=True, extra_tools=[bank])
            with_genes = Agent(model, "fake-model", hpo, seeded=True, extra_tools=tools)
        app = create_app(Diagnoser(hpo, agent=agent, agent_with_genes=with_genes), **options)
        return TestClient(app, raise_server_exceptions=False)

    return build


def scripted(*moves: AIMessage) -> ScriptedModel:
    return ScriptedModel(messages=iter(moves))


def test_health_checks_need_no_key_and_no_model(served: Served) -> None:
    http = served(api_key="s3cret")
    assert http.get("/healthz").json() == {"status": "ok"}
    ready = http.get("/readyz").json()
    assert ready == {"status": "ready", "hpo_release": "2099-01-01", "model_available": False}


def test_a_request_gets_an_answer_and_an_id(served: Served) -> None:
    http = served(scripted(answer(FITS), answer(FITS)))
    response = http.post("/v1/diagnose", json=BODY, headers={"X-Request-ID": "ward-7.42"})
    assert response.status_code == 200
    result = DiagnoseResponse.model_validate(response.json())
    assert (result.mode, result.diagnoses[0].disease_id) == ("agent", "OMIM:690001")
    assert result.request_id == response.headers["X-Request-ID"] == "ward-7.42"
    assert "not a medical device" in result.disclaimer
    # without an id of the caller's, or with one that is not a plain token, a new one
    made = http.post("/v1/diagnose", json=BODY, headers={"X-Request-ID": "a b\tc"})
    assert len(made.headers["X-Request-ID"]) == 32


@pytest.mark.parametrize(
    ("body", "said"),
    [
        ({"hpo_ids": ["hearing loss"]}, "String should match pattern"),
        ({"hpo_ids": []}, "at least 1 item"),
        (
            {"hpo_ids": [SNHL], "note": "Jane Doe, born 1 May 2019"},
            "Extra inputs are not permitted",
        ),
        ({"hpo_ids": [SNHL], "candidate_genes": ["not a gene!"]}, "String should match pattern"),
        ({"hpo_ids": [SNHL, "HP:1234567"]}, "not HPO terms in release 2099-01-01: HP:1234567"),
        ({"hpo_ids": ["HP:0000007"]}, "none of the terms is a phenotypic finding"),
    ],
)
def test_a_request_that_cannot_be_answered_is_refused_before_any_work(
    served: Served, body: dict[str, Any], said: str
) -> None:
    for path in ("/v1/diagnose", "/v1/diagnose/stream"):
        response = served().post(path, json=body)
        assert response.status_code == 422
        assert said in json.dumps(response.json())


def test_with_a_key_configured_the_api_needs_it(served: Served) -> None:
    http = served(api_key="s3cret")
    assert http.get("/v1/system").status_code == 401
    assert http.post("/v1/diagnose", json=BODY, headers={"X-API-Key": "wrong"}).status_code == 401
    assert http.post("/v1/diagnose", json=BODY, headers={"X-API-Key": "s3cret"}).status_code == 200
    with pytest.raises(ServiceError, match="401"):
        Client(http=http).system()
    assert Client(http=http, api_key="s3cret").system().model_available is False


def test_one_request_more_than_the_limit_is_told_to_retry(served: Served) -> None:
    response = served(max_concurrent=0).post("/v1/diagnose", json=BODY)
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert "busy" in response.json()["detail"]


class WaitingModel(GenericFakeChatModel):
    """A chat model that answers only when let go: holds a request open."""

    entered: Any = None
    release: Any = None

    def bind_tools(self, tools: Any, **kwargs: Any) -> "WaitingModel":
        return self

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        self.entered.set()
        self.release.wait(timeout=30)
        return super()._generate(messages, *args, **kwargs)


def test_room_is_held_while_a_request_is_answered_and_given_back_after(served: Served) -> None:
    entered, release = threading.Event(), threading.Event()
    model = WaitingModel(
        messages=iter([answer(FITS), answer(FITS)]), entered=entered, release=release
    )
    http = served(model, max_concurrent=1)
    statuses: list[int] = []
    first = threading.Thread(
        target=lambda: statuses.append(http.post("/v1/diagnose", json=BODY).status_code)
    )
    first.start()
    assert entered.wait(timeout=30)  # the first request is with the model
    assert http.post("/v1/diagnose", json=BODY).status_code == 503
    release.set()
    first.join(timeout=30)
    assert statuses == [200]
    assert http.post("/v1/diagnose", json=BODY).status_code == 200  # room again
    assert http.post("/v1/diagnose", json={"hpo_ids": ["HP:1234567"]}).status_code == 422
    assert http.post("/v1/diagnose/stream", json=BODY).status_code == 200  # and after a refusal


def test_the_stream_gives_each_step_then_the_answer(served: Served) -> None:
    http = served(
        scripted(
            call("check_match", hpo_ids=[SNHL, AMENORRHEA], disease_id="OMIM:690002"), answer(FITS)
        )
    )
    with http.stream("POST", "/v1/diagnose/stream", json=BODY) as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        wire = response.read().decode()
    assert wire.count("event: step") == 5 and wire.count("event: result") == 1

    http = served(
        scripted(
            call("check_match", hpo_ids=[SNHL, AMENORRHEA], disease_id="OMIM:690002"), answer(FITS)
        )
    )
    *steps, result = Client(http=http).stream(DiagnoseRequest(hpo_ids=[SNHL, AMENORRHEA]))
    assert all(isinstance(s, Step) for s in steps)
    assert isinstance(result, DiagnoseResponse)
    assert steps == result.steps and [s.kind for s in result.steps][-1] == "answer"
    assert result.diagnoses[0].disease_id == "OMIM:690001"


class BrokenModel(GenericFakeChatModel):
    def bind_tools(self, tools: Any, **kwargs: Any) -> "BrokenModel":
        return self

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        raise RuntimeError("a bug")


def test_a_failure_of_our_own_is_an_error_with_the_request_id(served: Served) -> None:
    http = served(BrokenModel(messages=iter([])))
    response = http.post("/v1/diagnose", json=BODY, headers={"X-Request-ID": "r-500"})
    assert response.status_code == 500
    assert response.json() == {"detail": "internal error", "request_id": "r-500"}
    with pytest.raises(ServiceError, match="internal error"):
        list(Client(http=http).stream(DiagnoseRequest(hpo_ids=[SNHL])))
    assert http.post("/v1/diagnose", json=BODY).status_code == 500  # room was given back


def test_the_log_line_counts_and_does_not_name_a_finding(
    served: Served, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="raredx.service"):
        served().post("/v1/diagnose", json=BODY, headers={"X-Request-ID": "r-log"})
    [line] = [r.getMessage() for r in caplog.records if r.name == "raredx.service"]
    logged = json.loads(line)
    assert (logged["request_id"], logged["mode"], logged["n_findings"]) == ("r-log", "fallback", 2)
    assert logged["trace_id"] and "seconds" in logged
    assert "HP:" not in line and "hearing" not in line.lower()


def test_through_http_a_request_is_still_one_trace_rooted_at_the_question(served: Served) -> None:
    http = served()
    mlflow.flush_trace_async_logging()  # the tests before this one have written theirs
    before = len(mlflow.search_traces(return_type="list"))
    http.get("/healthz")
    result = DiagnoseResponse.model_validate(http.post("/v1/diagnose", json=BODY).json())
    mlflow.flush_trace_async_logging()
    assert len(mlflow.search_traces(return_type="list")) == before + 1  # none for the check
    assert result.trace_id is not None
    trace = mlflow.get_trace(result.trace_id)
    assert trace is not None and trace.data.spans[0].name == "diagnose"
    assert trace.data.spans[0].parent_id is None


def test_terms_are_found_by_name(served: Served) -> None:
    client = Client(http=served())
    found = [(t.hpo_id, t.label) for t in client.terms("hearing")]
    assert found == [
        ("HP:0000365", "Hearing impairment"),  # names starting with the text first
        ("HP:0000407", "Sensorineural hearing impairment"),
        ("HP:0008619", "Bilateral sensorineural hearing impairment"),
    ]  # the obsolete "Old hearing term" is not offered
    assert client.terms("recessive") == []  # inheritance is not a finding
    with pytest.raises(ServiceError, match="422"):
        client.terms("h")


def test_examples_are_served_as_the_requests_the_evaluation_made(
    served: Served, hpo: HPO, make_case: Callable[..., Case]
) -> None:
    case_id, title, note = examples.listed()[0]
    case = make_case(
        case_id,
        hpo_ids=[SNHL, AMENORRHEA],
        hpo_labels=["SNHL", "Amenorrhea"],
        gene=None,
        sex="FEMALE",
        pmid="PMID:1001",
    )
    other = make_case("not listed")
    [example] = Client(http=served(examples=examples.load([other, case], hpo))).examples()
    assert (example.id, example.title, example.in_evaluation) == (case_id, title, note)
    assert example.request == DiagnoseRequest(
        hpo_ids=[SNHL, AMENORRHEA], sex="female", exclude_sources=["PMID:1001"]
    )
    assert example.candidate_genes is None  # no causal gene on record: nothing to sequence
    assert (example.confirmed_disease_id, example.source) == ("OMIM:621101", "PMID:1001")


def test_the_reference_documents_the_contract(served: Served) -> None:
    spec = served().get("/openapi.json").json()
    assert {"/v1/diagnose", "/v1/diagnose/stream", "/v1/system", "/v1/terms"} <= set(spec["paths"])
    request = spec["components"]["schemas"]["DiagnoseRequest"]
    assert request["additionalProperties"] is False
    assert set(request["properties"]) == {"hpo_ids", "sex", "candidate_genes", "exclude_sources"}

"""Reading a note through the service: the terms come back; the note stays out of the
log and the traces. The model is the real OpenAI SDK over a mocked network, so MLflow's
autologging records each model call exactly as it would in production."""

import json
import logging
from collections.abc import Callable, Iterator
from typing import Any

import httpx2
import mlflow
import pytest
from fastapi.testclient import TestClient
from openai import OpenAI

from raredx.knowledge.hpo import HPO
from raredx.knowledge.text_index import TextIndex
from raredx.phenotyping.reader import Label, NoteReader
from raredx.service import privacy
from raredx.service.app import create_app
from raredx.service.client import Client, ServiceError
from raredx.service.diagnoser import Diagnoser
from raredx.service.schemas import MAX_NOTE_CHARACTERS, NoteResponse

NOTE = "Jane Roe, born 3 May 2018, has had seizures since infancy. She cannot hear well."
SECRETS = ("Jane Roe", "3 May 2018", "since infancy", "cannot hear")


def completion(content: str) -> dict[str, Any]:
    return {
        "id": "c",
        "object": "chat.completion",
        "created": 0,
        "model": "m",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150},
    }


def model_over(*replies: str) -> OpenAI:
    """The OpenAI SDK, its HTTP answered by these replies in turn."""
    queue = list(replies)

    def answer(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=completion(queue.pop(0)))

    http = httpx2.Client(transport=httpx2.MockTransport(answer))
    return OpenAI(api_key="test", base_url="http://model.test/v1", http_client=http, max_retries=0)


READ = json.dumps(
    {
        "findings": [
            {"quote": "seizures", "finding": "Seizure", "status": "present"},
            {"quote": "cannot hear well", "finding": "Hearing difficulty", "status": "present"},
        ]
    }
)
LINKED = json.dumps({"codes": [{"n": 2, "hpo_id": "HP:0000365"}], "checked": []})


@pytest.fixture
def autologged() -> Iterator[None]:
    """MLflow's OpenAI autologging, as raredx.llm.client switches it on."""
    mlflow.openai.autolog()
    yield
    mlflow.openai.autolog(disable=True)


@pytest.fixture
def served(hpo: HPO, term_index: TextIndex[Label]) -> Callable[..., TestClient]:
    def build(*replies: str, reads: bool = True) -> TestClient:
        reader = NoteReader(model_over(*replies), "m", hpo, term_index) if reads else None
        diagnoser = Diagnoser(hpo, agent=None, agent_with_genes=None, prices=(0.3, 0.0, 1.2))
        app = create_app(diagnoser, reader=reader)
        return TestClient(app, raise_server_exceptions=False)

    return build


def test_a_note_is_read_into_terms_with_the_words_they_rest_on(
    served: Callable[..., TestClient], autologged: None
) -> None:
    result = Client(http=served(READ, LINKED)).read_note(NOTE)
    assert isinstance(result, NoteResponse)
    assert result.hpo_ids == ["HP:0001250", "HP:0000365"]
    assert [(f.quote, f.coded_by) for f in result.findings] == [
        ("seizures", "name"),
        ("cannot hear well", "model"),
    ]
    assert NOTE[result.findings[1].start : result.findings[1].end] == "cannot hear well"
    assert result.usage.model_calls == 2 and result.usage.input_tokens == 240
    assert result.usage.cost_usd_estimate == pytest.approx((240 * 0.3 + 60 * 1.2) / 1e6)
    assert "kept nowhere here" in result.notice


def test_the_trace_keeps_the_steps_and_the_codes_and_no_word_of_the_note(
    served: Callable[..., TestClient], autologged: None
) -> None:
    result = Client(http=served(READ, LINKED)).read_note(NOTE)
    mlflow.flush_trace_async_logging()
    trace = mlflow.get_trace(result.trace_id or "")
    assert trace is not None
    recorded = trace.to_json()
    for secret in SECRETS:
        assert secret not in recorded
    names = [s.name for s in trace.data.spans]
    assert names[0] == "note" and "read note" in names and "candidate terms" in names
    calls = [s for s in trace.data.spans if s.span_type == "CHAT_MODEL"]
    assert len(calls) == 2  # each model call is still there, with its timing ...
    assert all(s.inputs == privacy.REDACTED == s.outputs for s in calls)  # ... not its text
    root = trace.data.spans[0]
    assert root.inputs == {"characters": len(NOTE)}
    assert root.outputs["present"] == ["HP:0001250", "HP:0000365"]


def test_a_reply_the_model_cannot_put_right_fails_without_quoting_it(
    served: Callable[..., TestClient], autologged: None, caplog: pytest.LogCaptureFixture
) -> None:
    garbled = "Here are the findings: Jane Roe has seizures"
    http = served(garbled, garbled)
    with caplog.at_level(logging.INFO):
        response = http.post("/v1/terms/from-note", json={"text": NOTE})
    assert response.status_code == 502
    assert response.json()["detail"] == "the model's reply was not in the required format"
    for record in caplog.records:
        assert not any(secret in record.getMessage() for secret in SECRETS)
    mlflow.flush_trace_async_logging()
    [last] = mlflow.search_traces(return_type="list", max_results=1, order_by=["timestamp_ms DESC"])
    assert last.data.spans[0].name == "note"  # the failed reading's own trace
    assert not any(secret in last.to_json() for secret in SECRETS)


def test_the_log_line_counts_and_does_not_quote(
    served: Callable[..., TestClient], caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="raredx.service"):
        served(READ, LINKED).post("/v1/terms/from-note", json={"text": NOTE})
    [line] = [r.getMessage() for r in caplog.records if r.name == "raredx.service"]
    logged = json.loads(line)
    assert (logged["event"], logged["characters"], logged["n_present"]) == ("note", len(NOTE), 2)
    assert not any(secret in line for secret in SECRETS)


def test_a_service_that_takes_no_notes_has_no_such_endpoint(
    served: Callable[..., TestClient],
) -> None:
    http = served(reads=False)
    assert http.post("/v1/terms/from-note", json={"text": NOTE}).status_code == 404
    assert Client(http=http).system().note_reader is None
    assert Client(http=served()).system().note_reader["reader"] == "note-reader"  # type: ignore[index]


@pytest.mark.parametrize(
    "body", [{"text": ""}, {"text": "x" * (MAX_NOTE_CHARACTERS + 1)}, {"text": "x", "name": "J"}]
)
def test_an_empty_an_overlong_or_an_extended_request_is_refused(
    served: Callable[..., TestClient], body: dict[str, Any]
) -> None:
    assert served().post("/v1/terms/from-note", json=body).status_code == 422


def test_spans_outside_a_note_are_recorded_as_they_are() -> None:
    with mlflow.start_span(name="plain") as span:
        span.set_inputs({"hpo_ids": ["HP:0001250"]})
    mlflow.flush_trace_async_logging()
    trace = mlflow.get_trace(span.trace_id)
    assert trace is not None and trace.data.spans[0].inputs == {"hpo_ids": ["HP:0001250"]}


def test_the_client_says_when_the_service_cannot_read_it(
    served: Callable[..., TestClient],
) -> None:
    with pytest.raises(ServiceError, match="502"):
        Client(http=served("not json", "still not json")).read_note(NOTE)

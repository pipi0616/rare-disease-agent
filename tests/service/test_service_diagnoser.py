"""One request through the Diagnoser, on the miniature HPO release with a scripted model:
no network, no cost. The agent, its tools, the fallback and the trace are real."""

import itertools
from collections.abc import Iterator
from typing import Any

import httpx2
import mlflow
import openai
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult

from conftest import ScriptedModel, answer, call
from raredx.agent import FILLED, Agent
from raredx.data.cases import Case
from raredx.knowledge.hpo import HPO
from raredx.service.diagnoser import Diagnoser, NoFinding, UnknownTerms
from raredx.service.schemas import DiagnoseRequest, Step
from raredx.tools.find_similar_patients import FindSimilarPatients
from raredx.tools.rank_candidate_genes import RankCandidateGenes

SNHL, AMENORRHEA, SEIZURE = "HP:0000407", "HP:0000786", "HP:0001250"
PATIENT = DiagnoseRequest(hpo_ids=[SNHL, AMENORRHEA])
FITS = ("OMIM:690001", "Hearing-ovarian syndrome", "explains both findings")


def diagnoser(hpo: HPO, patients: list[Case], model: Any = None, **options: Any) -> Diagnoser:
    """A Diagnoser built as `raredx serve` builds it; without a model, the fallback alone."""
    if model is None:
        return Diagnoser(hpo, agent=None, agent_with_genes=None, **options)
    bank = FindSimilarPatients(hpo, patients, "test bank")
    return Diagnoser(
        hpo,
        agent=Agent(model, "fake-model", hpo, seeded=True, extra_tools=[bank]),
        agent_with_genes=Agent(
            model, "fake-model", hpo, seeded=True, extra_tools=[bank, RankCandidateGenes(hpo)]
        ),
        **options,
    )


def scripted(*moves: AIMessage) -> ScriptedModel:
    return ScriptedModel(messages=iter(moves))


class BrokenModel(GenericFakeChatModel):
    """A chat model whose every call raises the given error."""

    error: Any = None
    calls: int = 0

    def bind_tools(self, tools: Any, **kwargs: Any) -> "BrokenModel":
        return self

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        self.calls += 1
        raise self.error


def test_the_agent_answers_with_evidence_and_an_account_of_its_steps(
    hpo: HPO, patients: list[Case]
) -> None:
    model = scripted(
        call("check_match", hpo_ids=[SNHL, AMENORRHEA], disease_id="OMIM:690002"), answer(FITS)
    )
    seen: list[Step] = []
    result = diagnoser(hpo, patients, model).diagnose(PATIENT, request_id="r1", on_step=seen.append)

    assert (result.mode, result.fallback_reason, result.request_id) == ("agent", None, "r1")
    first = result.diagnoses[0]
    assert (first.rank, first.disease_id, first.reason) == (1, "OMIM:690001", FITS[2])
    assert first.evidence is not None
    assert [e.finding.hpo_id for e in first.evidence.match.explained] == [SNHL, AMENORRHEA]
    assert first.evidence.match.explained[0].sources == ["PMID:1001"]  # the evidence is cited
    assert first.evidence.inheritance == ["Autosomal recessive inheritance"]
    assert first.evidence.genes == ["GENEA"]
    # the seeded agent fills its list from the tools' order, and says so
    assert all(d.reason == FILLED for d in result.diagnoses[1:]) and len(result.diagnoses) > 1

    assert [s.kind for s in result.steps] == ["tools", "model", "tool", "model", "answer"]
    assert seen == result.steps  # each step was handed on as it happened, in order
    assert [s.n for s in seen] == [1, 2, 3, 4, 5]
    titles = [s.title for s in result.steps]
    assert titles[0].startswith("Phenotype tools: 5 diseases ranked")
    assert "Hearing-ovarian syndrome (2/2 findings)" in (result.steps[0].detail or "")
    assert titles[1:4] == [
        "Model, turn 1: asks the tools",
        "check_match: Hearing-retina syndrome",
        "Model, turn 2: gives its answer",
    ]
    assert result.steps[2].detail == "explains 1 of 2 findings"
    assert result.usage.model_calls == 2
    assert result.system.model_available and result.system.agent is not None
    assert result.system.agent["prompt_version"] == "seeded-v2"


def test_without_a_model_the_tools_ranking_answers_and_says_so(
    hpo: HPO, patients: list[Case]
) -> None:
    service = diagnoser(hpo, patients, unavailable_because="no model API key is configured")
    result = service.diagnose(PATIENT, request_id="r2")
    assert (result.mode, result.fallback_reason) == ("fallback", "no model API key is configured")
    assert result.diagnoses[0].disease_id == "OMIM:690001"  # rank-then-check's first
    assert result.diagnoses[0].reason is None and result.diagnoses[0].evidence is not None
    assert [s.kind for s in result.steps] == ["tools", "fallback"]
    assert result.usage.model_calls == 0 and result.usage.cost_usd_estimate == 0
    assert not result.system.model_available and result.system.agent is None


REQUEST = httpx2.Request("POST", "https://api.example/chat/completions")


@pytest.mark.parametrize(
    ("error", "said"),
    [
        (openai.APIConnectionError(request=REQUEST), "the model API failed (APIConnectionError)"),
        (
            openai.APIStatusError(
                "Insufficient Balance", response=httpx2.Response(402, request=REQUEST), body=None
            ),
            "the model API failed (APIStatusError 402)",
        ),
    ],
)
def test_when_the_model_api_fails_the_fallback_answers(
    hpo: HPO, patients: list[Case], error: Exception, said: str
) -> None:
    model = BrokenModel(messages=iter([]), error=error)
    result = diagnoser(hpo, patients, model).diagnose(PATIENT, request_id="r3")
    assert (result.mode, result.fallback_reason) == ("fallback", said)
    assert result.diagnoses[0].disease_id == "OMIM:690001"
    assert result.steps[-1].title == f"Model not used: {said}"


def test_an_agent_that_gives_no_final_answer_falls_back(hpo: HPO, patients: list[Case]) -> None:
    endless = (call("rank_diseases", hpo_ids=[SNHL]) for _ in itertools.count())
    model = ScriptedModel(messages=endless)
    result = diagnoser(hpo, patients, model).diagnose(PATIENT, request_id="r4")
    assert (result.mode, result.fallback_reason) == ("fallback", "the agent gave no final answer")
    assert result.usage.model_calls == 8  # it used its whole budget first


def test_a_failure_of_our_own_is_raised_not_papered_over(hpo: HPO, patients: list[Case]) -> None:
    model = BrokenModel(messages=iter([]), error=RuntimeError("a bug"))
    with pytest.raises(RuntimeError, match="a bug"):
        diagnoser(hpo, patients, model).diagnose(PATIENT, request_id="r5")


def test_past_its_deadline_the_agent_stops_before_its_next_model_call(
    hpo: HPO, patients: list[Case]
) -> None:
    model = BrokenModel(messages=iter([]), error=AssertionError("the model was called"))
    service = diagnoser(hpo, patients, model, deadline_seconds=-1.0)
    result = service.diagnose(PATIENT, request_id="r6")
    assert result.mode == "fallback" and "deadline" in (result.fallback_reason or "")
    assert model.calls == 0


def test_when_the_caller_is_gone_the_agent_stops_before_its_next_model_call(
    hpo: HPO, patients: list[Case]
) -> None:
    model = BrokenModel(messages=iter([]), error=AssertionError("the model was called"))
    result = diagnoser(hpo, patients, model).diagnose(
        PATIENT, request_id="r7", cancelled=lambda: True
    )
    assert (result.mode, result.fallback_reason) == ("fallback", "the caller went away")
    assert model.calls == 0


def test_an_unknown_term_is_refused_not_dropped(hpo: HPO, patients: list[Case]) -> None:
    request = DiagnoseRequest(hpo_ids=[SNHL, "HP:1234567"])
    with pytest.raises(UnknownTerms, match="HP:1234567") as refused:
        diagnoser(hpo, patients).findings(request)
    assert refused.value.terms == ["HP:1234567"]


def test_an_obsolete_term_is_replaced_and_a_repeat_dropped(hpo: HPO, patients: list[Case]) -> None:
    request = DiagnoseRequest(hpo_ids=["HP:0099999", SNHL, AMENORRHEA])
    findings = diagnoser(hpo, patients).findings(request)
    assert [(f.hpo_id, f.given_as) for f in findings] == [(SNHL, "HP:0099999"), (AMENORRHEA, None)]
    assert findings[0].label == "Sensorineural hearing impairment"


def test_terms_that_describe_no_finding_are_refused(hpo: HPO, patients: list[Case]) -> None:
    with pytest.raises(NoFinding):
        diagnoser(hpo, patients).findings(DiagnoseRequest(hpo_ids=["HP:0000007"]))


def test_with_candidate_genes_the_agent_of_the_genotype_track_answers(
    hpo: HPO, patients: list[Case]
) -> None:
    model = scripted(answer(("OMIM:690002", "Hearing-retina syndrome", "fits the hearing loss")))
    request = DiagnoseRequest(hpo_ids=[SNHL, AMENORRHEA], candidate_genes=["GENEA", "GENEA"])
    result = diagnoser(hpo, patients, model).diagnose(request, request_id="r8")
    assert result.mode == "agent"
    # fused with the gene ranking: the disease of the one candidate gene comes first
    assert (result.diagnoses[0].disease_id, result.diagnoses[0].gene) == ("OMIM:690001", "GENEA")
    kinds = [(s.kind, s.title.split(":")[0]) for s in result.steps]
    assert kinds[:2] == [("tools", "Phenotype tools"), ("tools", "Gene tool")]
    assert result.steps[1].detail == "Leading: GENEA → Hearing-ovarian syndrome"
    assert "fused with the candidate-gene ranking" in (result.steps[-1].detail or "")
    assert result.system.agent_with_genes is not None
    assert result.system.agent_with_genes["tools"].endswith("rank_candidate_genes")


def test_with_candidate_genes_and_no_model_the_gene_ranking_answers(
    hpo: HPO, patients: list[Case]
) -> None:
    request = DiagnoseRequest(hpo_ids=[SNHL, AMENORRHEA], candidate_genes=["GENEB1"])
    result = diagnoser(hpo, patients).diagnose(request, request_id="r9")
    assert result.mode == "fallback"
    assert [(d.disease_id, d.gene) for d in result.diagnoses] == [("OMIM:690002", "GENEB1")]


def test_excluded_sources_are_masked_as_in_the_evaluation(hpo: HPO, patients: list[Case]) -> None:
    service = diagnoser(hpo, patients)
    listed = service.diagnose(DiagnoseRequest(hpo_ids=[AMENORRHEA]), request_id="r10")
    hidden = service.diagnose(
        DiagnoseRequest(hpo_ids=[AMENORRHEA], exclude_sources=["PMID:1004"]), request_id="r11"
    )
    # OMIM:690004 is known from PMID:1004 alone
    assert "OMIM:690004" in [d.disease_id for d in listed.diagnoses]
    assert "OMIM:690004" not in [d.disease_id for d in hidden.diagnoses]


def test_a_request_is_one_trace_shaped_like_an_evaluations(hpo: HPO, patients: list[Case]) -> None:
    model = scripted(answer(FITS))
    result = diagnoser(hpo, patients, model).diagnose(PATIENT, request_id="r12")
    mlflow.flush_trace_async_logging()
    assert result.trace_id is not None
    trace = mlflow.get_trace(result.trace_id)
    assert trace is not None
    root = trace.data.spans[0]
    assert (root.name, root.inputs["question"]["case_id"]) == ("diagnose", "r12")
    assert root.inputs["question"]["hpo_ids"] == [SNHL, AMENORRHEA]
    assert root.outputs["candidates"][0]["disease_id"] == "OMIM:690001"
    assert trace.info.tags["mode"] == "agent"
    assert trace.info.client_request_id == "r12"
    names = {s.name for s in trace.data.spans}
    assert {"no-model ranking", "evidence", "check_match", "rank_diseases"} <= names


def test_tokens_are_counted_and_priced(hpo: HPO, patients: list[Case]) -> None:
    def spent(message: AIMessage) -> AIMessage:
        message.usage_metadata = {
            "input_tokens": 1000,
            "output_tokens": 100,
            "total_tokens": 1100,
            "input_token_details": {"cache_read": 400},
        }
        return message

    moves: Iterator[AIMessage] = iter([spent(answer(FITS))])
    service = diagnoser(hpo, patients, ScriptedModel(messages=moves), prices=(1.0, 0.1, 2.0))
    usage = service.diagnose(PATIENT, request_id="r13").usage
    assert (usage.input_tokens, usage.cached_input_tokens, usage.output_tokens) == (1000, 400, 100)
    assert usage.cost_usd_estimate == pytest.approx((600 * 1.0 + 400 * 0.1 + 100 * 2.0) / 1e6)

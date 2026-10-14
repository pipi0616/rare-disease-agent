"""The MLflow-native harness, against a throwaway local store.

Each test runs mlflow.genai.evaluate for real (a few seconds), so the suite
proves the whole path: dataset, parallel evaluation, scorer, traces, rescoring.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx2
import mlflow
import pytest
from mlflow.entities import Feedback, SpanType
from openai import APIStatusError, RateLimitError

from raredx.data.cases import Case
from raredx.evals import harness as h
from raredx.evals.systems import Candidate, Oracle, Question
from raredx.knowledge import masking


@pytest.fixture
def harness(tmp_path: Path) -> h.Harness:
    return h.Harness(f"sqlite:///{tmp_path / 'mlflow.db'}", tmp_path / "mlruns")


@pytest.fixture
def cases(make_case: Callable[..., Case]) -> list[Case]:
    return [make_case("1"), make_case("2"), make_case("3", gene=None, disease_id="OMIM:188400")]


class Flaky:
    """Right about case 1, says nothing useful about 2, crashes on 3."""

    name = "flaky"

    def predict(self, question: Question) -> list[Candidate]:
        if question.case_id == "3":
            raise TimeoutError("model did not answer")
        if question.case_id == "2":
            return [Candidate(disease_name="Something else", disease_id="OMIM:100000")]
        return [Candidate(disease_name="Perrault syndrome 7", disease_id="621101", gene="DAP3")]


def checks(outputs: Any, expectations: dict[str, Any]) -> dict[str, Any]:
    """The scorer's verdicts by name."""
    result = h.diagnosis(outputs=outputs, expectations=expectations)
    assert isinstance(result, list)
    return {f.name: f.value for f in result if isinstance(f, Feedback)}


def test_the_scorer_applies_the_rules() -> None:
    answer = {"candidates": [{"disease_name": "x", "disease_id": "OMIM:621101", "gene": "DAP3"}]}
    verdicts = checks(answer, {"disease_id": "OMIM:621101", "gene": "DAP3"})
    assert verdicts["answered"] and verdicts["disease_top1"] and verdicts["gene_top1"]
    assert not any(
        name.startswith("gene") for name in checks(answer, {"disease_id": "OMIM:621101"})
    )
    failed = checks(None, {"disease_id": "OMIM:621101"})
    assert failed["answered"] is False and failed["disease_top10"] is False


def test_a_record_never_puts_the_answer_in_the_inputs(cases: list[Case]) -> None:
    record = h.record_of(cases[0])
    assert "OMIM" not in str(record["inputs"]) and "DAP3" not in str(record["inputs"])
    assert record["expectations"] == {
        "disease_id": "OMIM:621101",
        "disease_label": "Perrault syndrome 7",
        "gene": "DAP3",
    }
    assert "gene" not in h.record_of(cases[2])["expectations"]


def test_oracle_scores_full_marks(harness: h.Harness, cases: list[Case]) -> None:
    _, summary = harness.evaluate(
        Oracle.from_cases(cases),
        "toy",
        "sha-1",
        cases,
        {"system": "oracle", "manifest": "toy", "manifest_sha256": "sha-1"},
    )
    assert summary.disease[1].rate == 1.0 and summary.gene[1].rate == 1.0
    assert summary.gene[1].n == 2  # the gene-less case is left out


def test_failures_are_misses_and_rescoring_reproduces_the_numbers(
    harness: h.Harness, cases: list[Case]
) -> None:
    params = {"system": "flaky", "manifest": "toy", "manifest_sha256": "sha-1"}
    run_id, summary = harness.evaluate(Flaky(), "toy", "sha-1", cases, params)
    assert (summary.n_cases, summary.n_answered, summary.disease[1].hits) == (3, 2, 1)

    new_id, again, _ = harness.rescore(run_id, "sha-1", expected=3)
    assert new_id != run_id and again == summary
    assert [r["name"] for r in harness.runs("toy")] == ["flaky (rescored)", "flaky"]


def test_a_changed_manifest_is_refused(harness: h.Harness, cases: list[Case]) -> None:
    params = {"system": "oracle", "manifest": "toy", "manifest_sha256": "sha-1"}
    run_id, _ = harness.evaluate(Oracle.from_cases(cases), "toy", "sha-1", cases, params)
    with pytest.raises(h.ManifestMismatch):
        harness.rescore(run_id, "sha-2", expected=3)
    with pytest.raises(h.ManifestMismatch):
        harness.dataset("toy", "sha-2", cases)


def test_a_run_with_lost_records_is_refused(
    harness: h.Harness, cases: list[Case], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If MLflow keeps fewer answers than cases asked, report an error, not a number."""
    monkeypatch.setattr(h.Harness, "traces", lambda self, run_id: [])
    params = {"system": "oracle", "manifest": "toy", "manifest_sha256": "sha-1"}
    with pytest.raises(h.IncompleteRun, match="only 0 of 3"):
        harness.evaluate(Oracle.from_cases(cases), "toy", "sha-1", cases, params)
    [failed] = harness.runs("toy")
    assert harness.client.get_run(failed["run_id"]).info.status == "FAILED"


class Peeker:
    """Notes what is masked from the tools' knowledge while it answers each case."""

    name = "peeker"

    def __init__(self) -> None:
        self.masked: dict[str, frozenset[str]] = {}

    def predict(self, question: Question) -> list[Candidate]:
        self.masked[question.case_id] = masking.current()
        return [Candidate(disease_name="Perrault syndrome 7", disease_id="OMIM:621101")]


def test_each_case_is_answered_with_its_own_source_paper_masked(
    harness: h.Harness, cases: list[Case]
) -> None:
    peeker = Peeker()
    params = {"system": "peeker", "manifest": "toy", "manifest_sha256": "sha-1"}
    run_id, _ = harness.evaluate(peeker, "toy", "sha-1", cases, params)
    assert peeker.masked == {c.id: {c.pmid} for c in cases}
    assert masking.current() == frozenset()  # and nothing afterwards
    assert harness.client.get_run(run_id).data.params["knowledge_mask"] == "case source paper"


def test_masking_can_be_turned_off_to_measure_a_leak(harness: h.Harness, cases: list[Case]) -> None:
    peeker = Peeker()
    params = {"system": "peeker", "manifest": "toy", "manifest_sha256": "sha-1"}
    run_id, _ = harness.evaluate(peeker, "toy", "sha-1", cases, params, mask_source_papers=False)
    assert set(peeker.masked.values()) == {frozenset()}
    run = harness.client.get_run(run_id)
    assert run.info.run_name == "peeker (unmasked)" and run.data.params["knowledge_mask"] == "none"


def test_each_cases_verdict_can_be_read_back_for_a_paired_comparison(
    harness: h.Harness, cases: list[Case]
) -> None:
    params = {"system": "flaky", "manifest": "toy", "manifest_sha256": "sha-1"}
    run_id, _ = harness.evaluate(Flaky(), "toy", "sha-1", cases, params)
    assert harness.hits(run_id, 1) == {"1": True, "2": False, "3": False}


class Leaky:
    """Its one tool shows each case's own paper, and a disease named per case."""

    name = "leaky"

    def __init__(self, leak: bool) -> None:
        self.leak = leak

    @mlflow.trace(span_type=SpanType.TOOL)
    def tool(self, case_id: str) -> dict[str, str]:
        return {"source": f"PMID:{case_id}" if self.leak else "PMID:99", "disease": "OMIM:600001"}

    def predict(self, question: Question) -> list[Candidate]:
        self.tool(question.case_id)
        return [Candidate(disease_name="x", disease_id="OMIM:100000")]


def test_a_tool_that_shows_the_cases_own_paper_fails_the_leak_audit(
    harness: h.Harness, cases: list[Case]
) -> None:
    params = {"system": "leaky", "manifest": "toy"}
    clean, _ = harness.evaluate(Leaky(leak=False), "toy", "sha-1", cases, params)
    run = harness.client.get_run(clean).data
    assert run.tags["leak_audit"] == "passed"
    assert run.metrics["leak/tool_outputs_read"] == 3 and run.metrics["leak/own_paper_shown"] == 0

    leaky, _ = harness.evaluate(Leaky(leak=True), "toy", "sha-1", cases, params)
    run = harness.client.get_run(leaky).data
    assert run.tags["leak_audit"] == "failed" and run.metrics["leak/own_paper_shown"] == 3


def test_the_audit_also_looks_for_diseases_known_only_from_the_paper(
    harness: h.Harness, cases: list[Case]
) -> None:
    def hidden_of(pmid: str) -> set[str]:
        return {"OMIM:600001"} if pmid == "PMID:2" else set()

    params = {"system": "leaky", "manifest": "toy"}
    run_id, _ = harness.evaluate(
        Leaky(leak=False), "toy", "sha-1", cases, params, hidden_of=hidden_of
    )
    run = harness.client.get_run(run_id).data
    assert run.metrics["leak/hidden_disease_shown"] == 1 and run.tags["leak_audit"] == "failed"


def test_a_paper_id_is_not_mistaken_for_a_longer_one(harness: h.Harness, cases: list[Case]) -> None:
    class Near(Leaky):
        @mlflow.trace(span_type=SpanType.TOOL)
        def tool(self, case_id: str) -> dict[str, str]:
            return {"source": f"PMID:{case_id}0"}  # PMID:10 is not PMID:1

    run_id, _ = harness.evaluate(Near(leak=True), "toy", "sha-1", cases, {"system": "near"})
    assert harness.client.get_run(run_id).data.tags["leak_audit"] == "passed"


def test_a_system_that_reads_no_tool_outputs_is_not_called_a_pass(
    harness: h.Harness, cases: list[Case]
) -> None:
    run_id, _ = harness.evaluate(Oracle.from_cases(cases), "toy", "sha-1", cases, {"system": "o"})
    assert harness.client.get_run(run_id).data.tags["leak_audit"] == "no tool outputs"


def test_the_genotype_track_puts_the_candidate_genes_in_the_question(cases: list[Case]) -> None:
    record = h.record_of(cases[0], ["GENEA", "DAP3"])
    assert record["inputs"]["question"]["candidate_genes"] == ["GENEA", "DAP3"]
    assert h.record_of(cases[0])["inputs"]["question"]["candidate_genes"] is None


def test_a_genotype_run_records_its_own_dataset(harness: h.Harness, cases: list[Case]) -> None:
    genes = {c.id: ["DAP3", "GENEA"] for c in cases}
    params = {"system": "oracle", "manifest": "toy", "label": "toy+genes"}
    harness.evaluate(Oracle.from_cases(cases), "toy+genes", "sha-g", cases, params, genes=genes)
    dataset = harness.dataset("toy+genes", "sha-g", cases, genes)
    assert dataset.name == "toy+genes"


class OutOfCredit:
    """Fails every case the way the model API does when the account has no credit."""

    name = "out-of-credit"

    def predict(self, question: Question) -> list[Candidate]:
        raise APIStatusError(
            "Error code: 402 - Insufficient Balance",
            response=httpx2.Response(402, request=httpx2.Request("POST", "https://api.test")),
            body=None,
        )


class Busy:
    """Rate-limited on its first attempt at each case and right on the second, as a new
    account at a model provider is: MLflow's evaluate asks the case again."""

    name = "busy"

    def __init__(self) -> None:
        self.tried: set[str] = set()

    def predict(self, question: Question) -> list[Candidate]:
        if question.case_id not in self.tried:
            self.tried.add(question.case_id)
            response = httpx2.Response(429, request=httpx2.Request("POST", "https://api.test"))
            raise RateLimitError("Rate limit exceeded: new accounts", response=response, body=None)
        return [Candidate(disease_name="Perrault syndrome 7", disease_id="OMIM:621101")]


def test_a_case_asked_again_after_a_rate_limit_counts_once_by_its_last_attempt(
    harness: h.Harness, cases: list[Case]
) -> None:
    run_id, summary = harness.evaluate(Busy(), "toy", "sha-1", cases, {"system": "busy"})
    assert len(harness.traces(run_id)) == 6  # every attempt is recorded
    assert len(harness.answers(run_id)) == 3  # one answer per case: the run is complete
    assert summary.n_answered == 3
    assert harness.hits(run_id, 1) == {"1": True, "2": True, "3": False}
    assert harness.client.get_run(run_id).data.metrics["errors/model_api"] == 0


def test_a_model_api_failure_is_counted_apart_from_the_systems_misses(
    harness: h.Harness, cases: list[Case]
) -> None:
    run_id, _ = harness.evaluate(OutOfCredit(), "toy", "sha-1", cases, {"system": "x"})
    run = harness.client.get_run(run_id).data
    assert run.metrics["errors/model_api"] == 3
    assert "Insufficient Balance" in run.tags["model_api_errors"]
    flaky, _ = harness.evaluate(Flaky(), "toy", "sha-1", cases, {"system": "flaky"})
    assert harness.client.get_run(flaky).data.metrics["errors/model_api"] == 0  # its own error

"""The MLflow-native harness, against a throwaway local store.

Each test runs mlflow.genai.evaluate for real (a few seconds), so the suite
proves the whole path: dataset, parallel evaluation, scorer, traces, rescoring.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from mlflow.entities import Feedback

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

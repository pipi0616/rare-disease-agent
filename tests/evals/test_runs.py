"""Run folders: what is saved, failures recorded, scores reproducible from disk."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from raredx.data.cases import Case
from raredx.evals import runs, splits
from raredx.evals.systems import Candidate, Oracle, Question


@pytest.fixture
def cases(make_case: Callable[..., Case]) -> list[Case]:
    return [make_case(str(i)) for i in range(5)]


@pytest.fixture
def manifest(cases: list[Case], tmp_path: Path) -> Path:
    path = tmp_path / "toy.tsv"
    path.write_text(splits.render(sorted((c.id, c.pmid) for c in cases)))
    return path


class Flaky:
    name = "flaky"

    def predict(self, question: Question) -> list[Candidate]:
        if question.case_id == "3":
            raise TimeoutError("model did not answer")
        return [Candidate(disease_name="Perrault syndrome 7", disease_id="621101")]


def test_a_run_folder_records_what_ran(cases: list[Case], manifest: Path, tmp_path: Path) -> None:
    run_dir = runs.start(tmp_path / "runs", "oracle", manifest, {"source": "toy"})
    runs.execute(Oracle.from_cases(cases), cases, run_dir)
    runs.score(run_dir, {c.id: c for c in cases})
    assert {p.name for p in run_dir.iterdir()} == {
        "meta.json",
        "predictions.jsonl",
        "scores.json",
        "per_case.jsonl",
    }
    meta = json.loads((run_dir / "meta.json").read_text())
    assert meta["system"] == "oracle" and meta["dataset"] == {"source": "toy"}
    assert len(meta["manifest_sha256"]) == 64


def test_a_failure_is_recorded_and_scored_as_a_miss(
    cases: list[Case], manifest: Path, tmp_path: Path
) -> None:
    run_dir = runs.start(tmp_path / "runs", "flaky", manifest, {})
    runs.execute(Flaky(), cases, run_dir)
    records = [
        json.loads(line) for line in (run_dir / "predictions.jsonl").read_text().splitlines()
    ]
    assert [r["error"] for r in records if r["error"]] == ["TimeoutError: model did not answer"]
    summary = runs.score(run_dir, {c.id: c for c in cases})
    assert (summary.n_cases, summary.n_answered, summary.disease[1].hits) == (5, 4, 4)


def test_rescoring_from_disk_gives_the_same_numbers(
    cases: list[Case], manifest: Path, tmp_path: Path
) -> None:
    run_dir = runs.start(tmp_path / "runs", "flaky", manifest, {})
    runs.execute(Flaky(), cases, run_dir)
    by_id = {c.id: c for c in cases}
    assert runs.score(run_dir, by_id) == runs.score(run_dir, by_id)


def test_scoring_refuses_a_manifest_that_changed(
    cases: list[Case], manifest: Path, tmp_path: Path
) -> None:
    run_dir = runs.start(tmp_path / "runs", "oracle", manifest, {})
    runs.execute(Oracle.from_cases(cases), cases, run_dir)
    manifest.write_text(manifest.read_text() + "extra\tPMID:9\n")
    with pytest.raises(ValueError, match="changed since this run"):
        runs.score(run_dir, {c.id: c for c in cases})

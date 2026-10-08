"""MLflow tracking against a throwaway local store: what a run records, and reading it back."""

from collections.abc import Callable
from pathlib import Path

import pytest

from raredx.data.cases import Case
from raredx.evals import runs
from raredx.evals.systems import Oracle
from raredx.evals.tracking import Tracker, experiment_name


@pytest.fixture
def tracker(tmp_path: Path) -> Tracker:
    return Tracker(f"sqlite:///{tmp_path / 'mlflow.db'}", tmp_path / "mlruns")


def log_oracle_run(tracker: Tracker, cases: list[Case]) -> str:
    records = runs.execute(Oracle.from_cases(cases), cases)
    summary, per_case = runs.score(records, [c.id for c in cases], {c.id: c for c in cases})
    return tracker.log(
        manifest="toy",
        run_name="oracle",
        params={"system": "oracle", "manifest": "toy", "code": "abc1234"},
        summary=summary,
        records=records,
        per_case=per_case,
    )


def test_a_run_records_params_metrics_and_answers(
    tracker: Tracker, make_case: Callable[..., Case]
) -> None:
    cases = [make_case(str(i)) for i in range(3)]
    run_id = log_oracle_run(tracker, cases)

    run = tracker.client.get_run(run_id)
    assert run.data.params["system"] == "oracle"
    assert run.data.metrics["disease_top1"] == 1.0
    assert run.data.metrics["n_cases"] == 3
    artifacts = {a.path for a in tracker.client.list_artifacts(run_id)}
    assert artifacts == {"predictions.jsonl", "per_case.jsonl", "scores.json"}


def test_saved_answers_come_back_unchanged(
    tracker: Tracker, make_case: Callable[..., Case]
) -> None:
    cases = [make_case(str(i)) for i in range(3)]
    run_id = log_oracle_run(tracker, cases)
    params, records = tracker.load(run_id)
    assert params["code"] == "abc1234"
    assert records == runs.execute(Oracle.from_cases(cases), cases)


def test_runs_on_one_manifest_share_an_experiment(
    tracker: Tracker, make_case: Callable[..., Case]
) -> None:
    cases = [make_case("1")]
    first, second = log_oracle_run(tracker, cases), log_oracle_run(tracker, cases)
    assert [r["run_id"] for r in tracker.runs("toy")] == [second, first]
    assert tracker.client.get_experiment_by_name(experiment_name("toy")) is not None
    assert tracker.runs("never-run") == []

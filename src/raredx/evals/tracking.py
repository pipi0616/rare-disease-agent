"""Experiment tracking with MLflow: every evaluation run is recorded where teams record them.

Local by default: run records go into ./mlflow.db (SQLite) and their files into
./mlruns; `uv run mlflow ui` shows both in a browser. Pointing the tracking URI
at a shared MLflow server (or Databricks) is the only change a team needs.

One experiment per manifest — "eval/dev-200" — so the runs that can be compared
sit side by side. Each run records:

    params     system, manifest and its sha256, dataset version, code commit
    metrics    top-k rate with its 95% interval, for disease and gene; cases answered
    artifacts  predictions.jsonl (the answers), per_case.jsonl (ranks), scores.json

The predictions are kept so a run can be re-scored later without asking the
system again — for a model, without paying again.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")  # mlflow prints a setup hint on import

from mlflow import MlflowClient  # noqa: E402
from mlflow.entities import Metric, Param  # noqa: E402

from raredx.evals.runs import PredictionRecord  # noqa: E402
from raredx.evals.scoring import KS, CaseScore, Summary  # noqa: E402

PREDICTIONS = "predictions.jsonl"


def experiment_name(manifest: str) -> str:
    return f"eval/{manifest}"


def metrics_of(summary: Summary) -> dict[str, float]:
    values: dict[str, float] = {"n_cases": summary.n_cases, "n_answered": summary.n_answered}
    for target, rates in (("disease", summary.disease), ("gene", summary.gene)):
        for k in KS:
            values[f"{target}_top{k}"] = rates[k].rate
            values[f"{target}_top{k}_low"] = rates[k].low
            values[f"{target}_top{k}_high"] = rates[k].high
    return values


class Tracker:
    def __init__(self, tracking_uri: str, artifact_root: Path) -> None:
        self.client = MlflowClient(tracking_uri=tracking_uri)
        self.artifact_root = artifact_root

    def experiment_id(self, name: str) -> str:
        found = self.client.get_experiment_by_name(name)
        if found is not None:
            return str(found.experiment_id)
        location = (self.artifact_root / name.replace("/", "-")).resolve().as_uri()
        return str(self.client.create_experiment(name, artifact_location=location))

    def log(
        self,
        *,
        manifest: str,
        run_name: str,
        params: dict[str, Any],
        summary: Summary,
        records: list[PredictionRecord],
        per_case: list[CaseScore],
    ) -> str:
        """Record one evaluation run; returns its MLflow run id."""
        run = self.client.create_run(
            self.experiment_id(experiment_name(manifest)), run_name=run_name
        )
        run_id = str(run.info.run_id)
        now = int(time.time() * 1000)
        self.client.log_batch(
            run_id,
            metrics=[Metric(key, value, now, 0) for key, value in metrics_of(summary).items()],
            params=[Param(key, str(value)) for key, value in params.items()],
        )
        with tempfile.TemporaryDirectory() as tmp:
            files = {
                PREDICTIONS: "".join(r.model_dump_json() + "\n" for r in records),
                "per_case.jsonl": "".join(s.model_dump_json() + "\n" for s in per_case),
                "scores.json": summary.model_dump_json(indent=2) + "\n",
            }
            for filename, text in files.items():
                path = Path(tmp) / filename
                path.write_text(text, encoding="utf-8")
                self.client.log_artifact(run_id, str(path))
        self.client.set_terminated(run_id)
        return run_id

    def load(self, run_id: str) -> tuple[dict[str, str], list[PredictionRecord]]:
        """A logged run's params and saved predictions."""
        params = dict(self.client.get_run(run_id).data.params)
        with tempfile.TemporaryDirectory() as tmp:
            path = self.client.download_artifacts(run_id, PREDICTIONS, dst_path=tmp)
            lines = Path(path).read_text(encoding="utf-8").splitlines()
        return params, [PredictionRecord.model_validate_json(line) for line in lines]

    def runs(self, manifest: str) -> list[dict[str, Any]]:
        """Every run on a manifest, newest first: what ran, and its headline numbers."""
        found = self.client.get_experiment_by_name(experiment_name(manifest))
        if found is None:
            return []
        rows = []
        for run in self.client.search_runs(
            [found.experiment_id], order_by=["attributes.start_time DESC"]
        ):
            rows.append(
                {
                    "run_id": run.info.run_id,
                    "name": run.info.run_name,
                    "started": time.strftime(
                        "%Y-%m-%d %H:%M", time.localtime(run.info.start_time / 1000)
                    ),
                    "code": run.data.params.get("code", ""),
                    **{
                        k: run.data.metrics.get(k)
                        for k in ("disease_top1", "disease_top10", "gene_top10")
                    },
                }
            )
        return rows

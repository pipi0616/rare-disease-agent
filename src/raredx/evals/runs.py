"""A run: one system on one manifest, kept in its own folder under runs/.

    runs/<time>_<system>_<manifest>/
        meta.json          what ran: system, manifest and its checksum, dataset, code commit
        predictions.jsonl  one line per case: the ranked candidates, or the error
        scores.json        the summary
        per_case.jsonl     where the right disease and gene ranked, case by case

Running and scoring are separate steps. Predictions are kept, so the scorer can
be re-run without asking the system again — for a model, without paying again.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from raredx.data.cases import Case
from raredx.data.sources import sha256_of
from raredx.evals import scoring
from raredx.evals.splits import read as read_manifest
from raredx.evals.systems import Candidate, System, question_of

RESULT_PATHS = ("src", "evals", "pyproject.toml", "uv.lock")


class PredictionRecord(BaseModel):
    case_id: str
    candidates: list[Candidate]
    error: str | None = None


def code_version() -> str:
    """Short commit hash, with -dirty when files that affect results are uncommitted.

    Only code, manifests and dependencies count: a notebook saved with its
    outputs does not change what a run computes.
    """
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--", *RESULT_PATHS],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return commit + ("-dirty" if dirty else "")


def start(runs_dir: Path, system: str, manifest: Path, dataset: dict[str, Any]) -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    run_dir = runs_dir / f"{stamp}_{system}_{manifest.stem}"
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = runs_dir / f"{stamp}_{system}_{manifest.stem}_{suffix}"
    run_dir.mkdir(parents=True)
    meta = {
        "system": system,
        "manifest": str(manifest),
        "manifest_sha256": sha256_of(manifest),
        "dataset": dataset,
        "code": code_version(),
        "started": datetime.now().isoformat(timespec="seconds"),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return run_dir


def execute(system: System, cases: list[Case], run_dir: Path) -> None:
    """Ask the system about every case. A failure is recorded, not skipped."""
    with (run_dir / "predictions.jsonl").open("w", encoding="utf-8") as f:
        for case in cases:
            try:
                record = PredictionRecord(
                    case_id=case.id, candidates=system.predict(question_of(case))
                )
            except Exception as e:  # noqa: BLE001 — any failure becomes a recorded miss
                record = PredictionRecord(
                    case_id=case.id, candidates=[], error=f"{type(e).__name__}: {e}"
                )
            f.write(record.model_dump_json() + "\n")


def read_meta(run_dir: Path) -> dict[str, Any]:
    meta: dict[str, Any] = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    return meta


def score(run_dir: Path, cases_by_id: dict[str, Case]) -> scoring.Summary:
    """Score a run's saved predictions against the manifest it ran on."""
    meta = read_meta(run_dir)
    manifest = Path(meta["manifest"])
    if sha256_of(manifest) != meta["manifest_sha256"]:
        raise ValueError(f"{manifest} changed since this run; its scores would not be comparable")
    case_ids = [case_id for case_id, _ in read_manifest(manifest)]

    predictions: dict[str, list[Candidate]] = {}
    with (run_dir / "predictions.jsonl").open(encoding="utf-8") as f:
        for line in f:
            record = PredictionRecord.model_validate_json(line)
            predictions[record.case_id] = record.candidates
    outside = set(predictions) - set(case_ids)
    if outside:
        raise ValueError(f"{len(outside)} predictions are for cases not in {manifest.name}")

    per_case = [scoring.score_case(cases_by_id[i], predictions.get(i, [])) for i in case_ids]
    summary = scoring.summarize(per_case)
    with (run_dir / "per_case.jsonl").open("w", encoding="utf-8") as f:
        for s in per_case:
            f.write(s.model_dump_json() + "\n")
    (run_dir / "scores.json").write_text(summary.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return summary

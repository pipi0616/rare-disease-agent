"""A run: ask one system about every case in a manifest, then score the answers.

Running and scoring are separate steps. `execute` asks the system and keeps
every answer, failures included; `score` turns saved answers into numbers. The
answers are what gets recorded (see tracking.py), so scoring can be repeated
later — with new rules — without asking the system again.
"""

import subprocess

from pydantic import BaseModel

from raredx.data.cases import Case
from raredx.evals import scoring
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


def execute(system: System, cases: list[Case]) -> list[PredictionRecord]:
    """Ask the system about every case. A failure is recorded, not skipped."""
    records = []
    for case in cases:
        try:
            answer = system.predict(question_of(case))
            records.append(PredictionRecord(case_id=case.id, candidates=answer))
        except Exception as e:  # noqa: BLE001 — any failure becomes a recorded miss
            error = f"{type(e).__name__}: {e}"
            records.append(PredictionRecord(case_id=case.id, candidates=[], error=error))
    return records


def score(
    records: list[PredictionRecord], case_ids: list[str], cases_by_id: dict[str, Case]
) -> tuple[scoring.Summary, list[scoring.CaseScore]]:
    """Score saved answers against the cases of one manifest."""
    answers = {r.case_id: r.candidates for r in records}
    outside = set(answers) - set(case_ids)
    if outside:
        raise ValueError(f"{len(outside)} answers are for cases outside the manifest")
    per_case = [scoring.score_case(cases_by_id[i], answers.get(i, [])) for i in case_ids]
    return scoring.summarize(per_case), per_case

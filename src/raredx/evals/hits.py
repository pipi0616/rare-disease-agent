"""Per-case verdicts of several runs side by side: the table paired comparisons read.

One row per case of a manifest, one column per run and k: 1 if the run had the
confirmed disease in its top k, else 0. A run made on a larger manifest (all of
RAMEDIS) fills a table for a part of it (the 200 billed per case): the same case,
the same answer. The table also says whether each case was answerable at all.
"""

import csv
from pathlib import Path

from raredx.data.cases import Case
from raredx.evals.scoring import KS
from raredx.knowledge.hpo import HPO

Verdicts = dict[int, dict[str, bool]]  # k -> case id -> hit


def answerable(case: Case, hpo: HPO) -> bool:
    """Whether a system reading the masked knowledge could name the diagnosis at all:
    one of its accepted OMIM entries is a disease in the release, and not one known only
    from the case's own paper (which the mask makes not exist)."""
    accepted = [d for d in (case.disease_id, *case.also_accepted) if d in hpo.names]
    hidden = hpo.known_only_from(frozenset({case.pmid})) if case.pmid else set()
    return any(d not in hidden for d in accepted)


def table(cases: list[Case], runs: dict[str, Verdicts], hpo: HPO) -> list[dict[str, str]]:
    """The rows; every run must have answered every case."""
    for name, verdicts in runs.items():
        missing = {c.id for c in cases} - set(verdicts[KS[0]])
        if missing:
            raise ValueError(f"run {name} has no answer to {len(missing)} of these cases")
    rows = []
    for case in cases:
        row = {
            "case_id": case.id,
            "pmid": case.pmid or "",
            "answerable": str(int(answerable(case, hpo))),
        }
        for name, verdicts in runs.items():
            row |= {f"{name}@{k}": str(int(verdicts[k][case.id])) for k in KS}
        rows.append(row)
    return rows


def write(rows: list[dict[str, str]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

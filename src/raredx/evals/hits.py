"""Per-case verdicts of several runs side by side: the table paired comparisons read.

One row per case of a manifest, one column per run and k: 1 if the run had the
confirmed disease in its top k, else 0. A run made on a larger manifest (all of
RAMEDIS) fills a table for a part of it (the 200 billed per case): the same case,
the same answer. The table also says whether each case was answerable at all.
"""

import csv
from pathlib import Path

from raredx.data.cases import Case
from raredx.evals.scoring import KS, Same, accepted_ids
from raredx.knowledge.hpo import HPO

Verdicts = dict[int, dict[str, bool]]  # k -> case id -> hit


def answerable(case: Case, hpo: HPO, same: Same | None = None) -> bool:
    """Whether a system reading the masked knowledge could name the diagnosis at all:
    one of its accepted entries names a disease in the knowledge (through disease
    identity, when the knowledge has it), and not one known only from the case's own
    paper (which the mask makes not exist). With same, their equals count too, as the
    scorer given it accepts them: an Orphanet diagnosis is answerable from OMIM-only
    knowledge when Mondo makes it equal to an OMIM disease there."""
    named = (hpo.canonical(d) for d in accepted_ids(case.disease_id, case.also_accepted, same))
    accepted = [d for d in named if d is not None]
    hidden = hpo.known_only_from(frozenset({case.pmid})) if case.pmid else set()
    return any(d not in hidden for d in accepted)


def combine(parts: list[tuple[Verdicts, set[str]]]) -> tuple[Verdicts, set[str]]:
    """A run and the runs that asked again what it lost (--fill-in), in order, as one:
    each (verdicts, cases lost to the model API). A later answer replaces an earlier
    one; what is still lost at the end is returned, to be refused."""
    verdicts: Verdicts = {k: {} for k in KS}
    lost: set[str] = set()
    for got, lost_here in parts:
        lost = (lost - set(got[KS[0]])) | lost_here
        for k in KS:
            verdicts[k] |= got[k]
    return verdicts, lost


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

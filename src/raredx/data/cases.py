"""The case model every dataset is converted into, and its processed file.

Whatever the source, a case ends up as a `Case`: observed phenotype, confirmed
diagnosis, causal gene and variants, source paper. Everything downstream —
manifests, the scorer, the agent — reads cases from the processed layer, never
from a raw download.

The pinned Phenopacket Store release is split in two, design and heldout. Cases
from anywhere else — the store's later cases, another dataset — are "external":
only ever tested on, never developed against, never in the patient bank.
"""

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

Split = Literal["design", "heldout", "external"]


class Variant(BaseModel):
    gene: str
    hgvs_c: str | None = None
    hgvs_p: str | None = None
    zygosity: str = "unknown"


class Case(BaseModel):
    id: str
    cohort: str  # the store's folder, usually the gene or syndrome name
    hpo_ids: list[str]  # features the authors observed; `excluded` ones are dropped
    hpo_labels: list[str]
    disease_id: str  # OMIM:nnnnnn, or the source's own code when it names no OMIM entry
    disease_label: str
    gene: str | None  # None for e.g. chromosomal-deletion cohorts
    variants: list[Variant]
    pmid: str | None  # PMID:nnnnnnnn — also decides the split; None: no paper (a clinic's)
    sex: str | None
    split: Split
    # Other OMIM entries that count as the diagnosis too: a source may list several for
    # one patient (RareBench does). Empty for Phenopacket Store: one disease per case.
    also_accepted: list[str] = []


CASES_FILE = "cases.jsonl"
BUILD_FILE = "build.json"


def write(cases: list[Case], out_dir: Path, build_info: dict[str, Any]) -> Path:
    """One case per line, sorted by id, plus a build.json saying what it was built from."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / CASES_FILE
    with path.open("w", encoding="utf-8") as f:
        for case in sorted(cases, key=lambda c: c.id):
            f.write(case.model_dump_json() + "\n")
    (out_dir / BUILD_FILE).write_text(json.dumps(build_info, indent=2) + "\n", encoding="utf-8")
    return path


def read(out_dir: Path) -> list[Case]:
    with (out_dir / CASES_FILE).open(encoding="utf-8") as f:
        return [Case.model_validate_json(line) for line in f]


def read_build_info(out_dir: Path) -> dict[str, Any]:
    info: dict[str, Any] = json.loads((out_dir / BUILD_FILE).read_text(encoding="utf-8"))
    return info

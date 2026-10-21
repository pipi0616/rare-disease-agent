"""RareArena's rare-disease screening cases (RDS), as DeepRare distributes them.

Published case reports from PubMed Central (PMC-Patients): each a free-text report with
the patient's age and sex and an Orphanet diagnosis. DeepRare ships 10,000 of them as
its case bank (RDS_embeddings.csv, with an embedding per report this project does not
use). Here they are development cases unlike Phenopacket Store's: written by clinicians
rather than curated into HPO terms, and a third of their diagnoses are relatively
common rare diseases (Orphanet: one in 100,000 or more), which the held-out set hardly
has (5%).

Two cautions, both on record (docs/v2_design.md):
- the papers are older than the model's training cutoff, so the model may have read
  them: development data only, never a test;
- licence CC BY-NC-SA 4.0 (PMC-Patients, RareArena): non-commercial.

A report becomes a case once read into HPO terms (raredx.phenotyping.reader): only the
findings the report says the patient has. Its paper is masked like any case's, by the
PMID its PMC id maps to (NCBI's ID converter; the table is kept in evals/).
"""

import csv
import random
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

import httpx
from pydantic import BaseModel

FILE = "RDS_embeddings.csv"
IDCONV = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
BATCH = 200
HEADER = "pmcid\tpmid"


class Report(BaseModel):
    id: str  # "RareArena_<PMC number>-<patient>", as the cases will be named
    pmcid: str  # PMC4624164
    text: str
    disease_id: str  # ORPHA:458763
    disease_label: str
    age: str  # as written, e.g. "[[30.0, 'year']]"
    sex: str | None  # FEMALE, MALE, or unknown


def reports(path: Path) -> Iterator[Report]:
    """Every report in the file, in file order; the embedding column is not read."""
    csv.field_size_limit(1 << 30)
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            number = row["_id"]
            sex = {"F": "FEMALE", "M": "MALE"}.get(row["gender"].strip().upper())
            yield Report(
                id=f"RareArena_{number}",
                pmcid=f"PMC{number.split('-')[0]}",
                text=row["case_report"],
                disease_id=f"ORPHA:{row['Orpha_id'].strip()}",
                disease_label=row["Orpha_name"] or row["diagnosis"],
                age=row["age"],
                sex=sex,
            )


# ── PMC ids to PMIDs ────────────────────────────────────────────────


def convert(pmcids: list[str], client: httpx.Client | None = None) -> dict[str, str]:
    """Each paper's PMID (PMID:n) by its PMC id, from NCBI's ID converter, in batches.
    A paper NCBI does not map is left out."""
    own = client is None
    http = client or httpx.Client(timeout=60)
    found: dict[str, str] = {}
    try:
        for start in range(0, len(pmcids), BATCH):
            ids = ",".join(pmcids[start : start + BATCH])
            response = http.get(IDCONV, params={"ids": ids, "format": "json", "tool": "raredx"})
            response.raise_for_status()
            for record in response.json().get("records", []):
                if record.get("pmid"):
                    found[record["pmcid"]] = f"PMID:{record['pmid']}"
    finally:
        if own:
            http.close()
    return found


def read_pmids(path: Path) -> dict[str, str]:
    """The PMC id to PMID table kept in git."""
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != HEADER:
        raise ValueError(f"{path}: expected header {HEADER!r}")
    return dict(line.split("\t") for line in lines[1:] if line)


def update_pmids(path: Path, pmcids: set[str]) -> int:
    """Add the papers the table lacks; returns how many were added. A mapping does not
    change, so papers already listed are not asked again."""
    known = read_pmids(path)
    found = convert(sorted(pmcids - set(known)))
    known |= found
    path.write_text(
        HEADER + "\n" + "".join(f"{k}\t{known[k]}\n" for k in sorted(known)), encoding="utf-8"
    )
    return len(found)


# ── the development sample ──────────────────────────────────────────

SEED = 20261021
PER_DISEASE = 3
COMMON_SHARE = 1 / 3


def sample(
    candidates: list[Report],
    pmids: dict[str, str],
    band: dict[str, str],
    n: int,
    seed: int = SEED,
) -> list[Report]:
    """n reports by fixed rules: one per paper; at most PER_DISEASE per diagnosis; at
    least a third with a relatively common diagnosis (band "1 in 100,000 or more"), the
    rest drawn from all others; by a fixed seed. `candidates` are already filtered (a
    PMID, a diagnosis the knowledge has, no paper of the pinned Phenopacket Store)."""
    rng = random.Random(seed)
    by_paper: dict[str, list[Report]] = defaultdict(list)
    for report in candidates:
        by_paper[pmids[report.pmcid]].append(report)
    one_each = [rng.choice(sorted(rs, key=lambda r: r.id)) for _, rs in sorted(by_paper.items())]
    rng.shuffle(one_each)
    common = [r for r in one_each if band.get(r.disease_id) == "1 in 100,000 or more"]
    other = [r for r in one_each if band.get(r.disease_id) != "1 in 100,000 or more"]
    chosen: list[Report] = []
    per_disease: dict[str, int] = defaultdict(int)

    def take(pool: list[Report], until: int) -> None:
        for report in pool:
            if len(chosen) >= until:
                return
            if report in chosen or per_disease[report.disease_id] >= PER_DISEASE:
                continue
            chosen.append(report)
            per_disease[report.disease_id] += 1

    take(common, round(n * COMMON_SHARE))
    take(other + common, n)
    return sorted(chosen, key=lambda r: r.id)

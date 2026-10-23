"""Similar published case reports: a nominating route over RareArena's reports.

DeepRare's largest component is retrieval of similar published cases. Here the bank is
the 10,000 case reports RareArena drew from PubMed Central (data.rarearena), each with
an Orphanet diagnosis, indexed for hybrid search (dense BGE + BM25, as the disease
texts). A patient's findings, as their HPO names, are the query; the diagnoses of the
most similar reports, best first and each once, are the route's candidates.

The mask: a report from the patient's own paper is never returned. Offline on the
development sources (chapter 32) the route's first ten diagnoses held the confirmed one
for 27% of HMS's clinic patients and 25% of RareArena's own development cases (other
papers only), and for 2–9% elsewhere; added to the model's and the phenotype
ranking's candidates it raised HMS's coverage from 59% to 66%.

Licence of the bank: CC BY-NC-SA 4.0 (non-commercial).
"""

from pathlib import Path

import numpy as np
from pydantic import BaseModel

from raredx.data import rarearena
from raredx.knowledge.text_index import Embedder, TextIndex

DEEP = 80  # reports read per query before the patient's own paper is dropped


class Report(BaseModel):
    id: str
    pmid: str
    disease_id: str
    text: str


def build(raw: Path, pmids: dict[str, str], embedder: Embedder, folder: Path) -> int:
    """Embed every report whose paper has a PMID and save the index; returns how many."""
    bank = [
        Report(id=r.id, pmid=pmids[r.pmcid], disease_id=r.disease_id, text=r.text)
        for r in rarearena.reports(raw)
        if r.pmcid in pmids
    ]
    dense, sparse = [], []
    for start in range(0, len(bank), 256):
        d, s = embedder.passages([b.text for b in bank[start : start + 256]])
        dense.append(d)
        sparse += s
    TextIndex.save(folder, bank, np.vstack(dense), sparse, {"what": "RareArena RDS reports"})
    return len(bank)


class CaseBank:
    """The index, searched with a patient's findings."""

    def __init__(self, index: TextIndex[Report]) -> None:
        self.index = index

    def similar(self, findings: list[str], own_paper: str | None) -> list[Report]:
        """The most similar reports, best first, none from the patient's own paper."""
        hits = self.index.search("; ".join(findings), limit=DEEP)
        return [r for r, _ in hits if not (own_paper and r.pmid == own_paper)]

    def nominate(self, findings: list[str], own_paper: str | None, k: int = 10) -> list[str]:
        """The diagnoses of the most similar reports, best first, each once, at most k."""
        diseases: list[str] = []
        for report in self.similar(findings, own_paper):
            if report.disease_id not in diseases:
                diseases.append(report.disease_id)
            if len(diseases) == k:
                break
        return diseases

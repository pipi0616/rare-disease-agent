"""Real patients from outside the published case reports: MyGene2 and CADA.

Every case the systems were developed on comes from a paper — Phenopacket Store, or
RareBench's sets — and HPO's annotations are curated from such papers. These two
sources hold patients as a clinic or a diagnostic laboratory recorded them.

MyGene2 (mygene2.org, University of Washington): families and clinicians share a
patient's features and the gene found. Read as SHEPHERD preprocessed it (Alsentzer et
al., npj Digital Medicine 2025; Harvard Dataverse doi:10.7910/DVN/TZTPFL, CC0): 146
patients with an OMIM diagnosis and one causal gene, as of May 2022. DeepRare (Nature
2026) reports on the same file. Each line is one patient: HPO terms, the OMIM number,
Orphanet codes, and for some a PubMed id.

CADA (Peng et al., NAR Genomics and Bioinformatics 2021; github.com/Chengyao-Peng/CADA,
GPL-3.0): 4,714 patients with a genetic diagnosis in one gene — ClinVar submissions
that carry HPO terms (from diagnostic laboratories, the Undiagnosed Diseases Network
among them) and patients of the authors' collaborators (Tübingen, Bonn, Berlin and
others). The authors' own split is kept: their test file is tested on, once; their
training file is developed on; their validation file is left unread. Each line is one
patient: an id, the OMIM diagnosis or "unknown", the NCBI gene id, the HPO terms, who
submitted it.

How a case is read, fixed before any system ran on either source:

- MyGene2's diagnosis is read by RareBench's rules (rarebench.diagnosis): the OMIM
  number, and any OMIM entry Orphanet maps exactly to an Orphanet code listed. The
  gene is given as an Ensembl id and is not read: the disease is what is scored.
- A CADA patient whose diagnosis is "unknown" names a gene and no disease: left out,
  and counted, because the systems here answer with diseases. The gene is read from
  its NCBI id through the pinned HPO release's gene table; one the table does not
  have leaves the case without a gene (it is scored on the disease alone).
- terms are read as the pinned HPO release has them, as for RareBench; a patient left
  with none is dropped.
- a PubMed id, where MyGene2 gives one, is the case's paper: masked while the case is
  asked, like any other case's. CADA names no paper.
"""

import json
import re
from collections import Counter
from pathlib import Path

from raredx.data import rarebench
from raredx.data.cases import Case
from raredx.evals.scoring import normalize_disease
from raredx.knowledge.hpo import HPO

MYGENE2 = "MyGene2"
CADA_PARTS = {
    "train": "cases_train.tsv",
    "validate": "cases_validate.tsv",
    "test": "cases_test.tsv",
}
CADA_READ = ("train", "test")  # the validation file is left unread


def _terms(written: list[str], hpo: HPO, dropped: Counter[str]) -> list[str]:
    terms: list[str] = []
    for term in written:
        current = hpo.current(term.strip())
        if current is None:
            dropped["unknown_term"] += 1
        elif current not in terms:
            terms.append(current)
    return terms


def load_mygene2(
    path: Path, hpo: HPO, orphanet: rarebench.Orphanet
) -> tuple[list[Case], Counter[str]]:
    """Every MyGene2 patient of SHEPHERD's file, plus counts of what was dropped."""
    cases: list[Case] = []
    dropped: Counter[str] = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        patient = json.loads(line)
        omim = normalize_disease(str(patient.get("omim") or ""))
        if omim is None:
            dropped["no_omim"] += 1
            continue
        terms = _terms(patient["positive_phenotypes"], hpo, dropped)
        if not terms:
            dropped["no_phenotype"] += 1
            continue
        codes = [omim, *(f"ORPHA:{int(code)}" for code in patient.get("orpha_id") or [])]
        disease, also, label = rarebench.diagnosis(codes, hpo, orphanet)
        if label == codes[0] and patient.get("disease_name"):
            label = str(patient["disease_name"])
        paper = patient.get("pubmed_id")
        cases.append(
            Case(
                id=f"MyGene2_{patient['id']}",
                cohort=MYGENE2,
                hpo_ids=terms,
                hpo_labels=[hpo.term(t)[1] for t in terms],
                disease_id=disease,
                disease_label=label,
                gene=None,
                variants=[],
                pmid=f"PMID:{int(paper)}" if paper else None,
                sex=None,
                split="external",
                also_accepted=also,
            )
        )
    return cases, dropped


def load_cada(folder: Path, hpo: HPO, symbols: dict[str, str]) -> tuple[list[Case], Counter[str]]:
    """CADA's training and test patients that have an OMIM diagnosis. `symbols`: NCBI
    gene id -> symbol (hpo.gene_symbols). The id says which of CADA's files a case is
    from (CADA_train_..., CADA_test_...); the cohort, who submitted it."""
    cases: list[Case] = []
    dropped: Counter[str] = Counter()
    for part in CADA_READ:
        for line in (folder / CADA_PARTS[part]).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            patient, diagnosis, gene, written, _, origin = line.split("\t")[:6]
            disease = normalize_disease(diagnosis) if diagnosis.startswith("OMIM:") else None
            if disease is None:
                dropped[f"{part}:no_disease"] += 1
                continue
            terms = _terms(written.split(","), hpo, dropped)
            if not terms:
                dropped[f"{part}:no_phenotype"] += 1
                continue
            name = re.sub(r"[^A-Za-z0-9]+", "-", patient.removeprefix("Patient:")).strip("-")
            symbol = symbols.get(gene.removeprefix("Entrez:"))
            if symbol is None:
                dropped[f"{part}:gene_not_in_hpo"] += 1  # kept, scored on the disease alone
            cases.append(
                Case(
                    id=f"CADA_{part}_{name}",
                    cohort=origin or "CADA",
                    hpo_ids=terms,
                    hpo_labels=[hpo.term(t)[1] for t in terms],
                    disease_id=disease,
                    disease_label=hpo.names.get(disease, disease),
                    gene=symbol,
                    variants=[],
                    pmid=None,
                    sex=None,
                    split="external",
                )
            )
    ids = Counter(c.id for c in cases)
    twice = sorted(i for i, n in ids.items() if n > 1)
    if twice:
        raise ValueError(f"CADA: {len(twice)} patient ids are not unique, e.g. {twice[0]}")
    return cases, dropped

"""RareBench (Chen et al., KDD 2024): public rare-disease patients from other sources.

Each line of data/<set>.jsonl is one patient: the HPO terms observed, and the
diagnosis as codes — OMIM, Orphanet (ORPHA) and China's rare-disease list (CCRD).
No sex, no gene, no source paper. Four sets are public:

    HMS      88 patients of a clinic at Hannover Medical School (Ronicke et al. 2019)
    RAMEDIS  624 cases of a registry of rare metabolic diseases (Töpel et al. 2010)
    MME      40 cases from published reports: Matchmaker Exchange's test set
    LIRICAL  370 cases from published reports: LIRICAL's own test set

All four are read; only HMS and RAMEDIS are tested on (evals/splits.py). MME and
LIRICAL come from case reports that HPO's annotations may cite, and they name no
paper to mask; LIRICAL's overlap the store's own patients (docs/external_plan.md).

How a diagnosis is read, fixed before any system ran on these sets:

- every OMIM code the patient lists counts as the diagnosis, and so does any OMIM
  entry Orphanet maps exactly (E) to an Orphanet code listed;
- disease_id is the first of those HPO knows as a disease, the rest go in
  also_accepted;
- a patient none of whose codes leads to an OMIM entry keeps its first code (say
  ORPHA:81). A system answering in OMIM cannot name it, so it is a miss, as such a
  patient would be in a clinic;
- terms are read as the pinned HPO release has them (an alternative id as its
  primary, an obsolete term as its replacement); a term it does not know is dropped.
"""

import json
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

from raredx.data.cases import Case
from raredx.knowledge.hpo import HPO
from raredx.knowledge.texts import EXACT

ARCHIVE = "data.zip"
SETS = ("HMS", "RAMEDIS", "MME", "LIRICAL")


class Orphanet:
    """Orphanet's disorders: each one's name, and the OMIM entries mapped to it exactly."""

    def __init__(self, path: Path) -> None:
        self.names: dict[str, str] = {}
        self.exact: dict[str, list[str]] = {}
        for disorder in ET.parse(path).getroot().iter("Disorder"):
            code = f"ORPHA:{disorder.findtext('OrphaCode')}"
            self.names[code] = disorder.findtext("Name") or ""
            self.exact[code] = sorted(
                {
                    f"OMIM:{ref.findtext('Reference')}"
                    for ref in disorder.iter("ExternalReference")
                    if ref.findtext("Source") == "OMIM"
                    and (ref.findtext("DisorderMappingRelation/Name") or "").startswith(EXACT)
                }
            )


def diagnosis(codes: list[str], hpo: HPO, orphanet: Orphanet) -> tuple[str, list[str], str]:
    """The patient's codes as (disease_id, also_accepted, label), by the rules above."""
    omim = [c for c in codes if c.startswith("OMIM:")]
    for code in codes:
        for entry in orphanet.exact.get(code, []):
            if entry not in omim:
                omim.append(entry)
    known = [c for c in omim if c in hpo.names]
    ordered = known + [c for c in omim if c not in known]
    if not ordered:
        first = codes[0]
        return first, [], orphanet.names.get(first, first)
    disease = ordered[0]
    label = hpo.names.get(disease) or next(
        (orphanet.names[c] for c in codes if c in orphanet.names), disease
    )
    return disease, ordered[1:], label


def load(archive: Path, hpo: HPO, orphanet: Orphanet) -> tuple[list[Case], Counter[str]]:
    """Every patient of the four sets, plus counts of what was dropped on the way."""
    cases: list[Case] = []
    dropped: Counter[str] = Counter()
    with zipfile.ZipFile(archive) as z:
        for name in SETS:
            lines = z.read(f"data/{name}.jsonl").decode("utf-8").splitlines()
            for i, line in enumerate(lines, 1):
                patient = json.loads(line)
                terms: list[str] = []
                for term in patient["Phenotype"]:
                    current = hpo.current(term)
                    if current is None:
                        dropped["unknown_term"] += 1
                    elif current not in terms:
                        terms.append(current)
                if not terms:
                    dropped["no_phenotype"] += 1
                    continue
                disease, also, label = diagnosis(patient["RareDisease"], hpo, orphanet)
                cases.append(
                    Case(
                        id=f"RareBench_{name}_{i:03d}",
                        cohort=name,
                        hpo_ids=terms,
                        hpo_labels=[hpo.term(t)[1] for t in terms],
                        disease_id=disease,
                        disease_label=label,
                        gene=None,
                        variants=[],
                        pmid=None,
                        sex=None,
                        split="external",
                        also_accepted=also,
                    )
                )
    return cases, dropped

"""Phenopacket Store: published, solved rare-disease cases, used as the evaluation set.

Each phenopacket is one patient from one published report: the HPO terms the
authors observed, the OMIM disease the case was solved as, the causal gene and
variants, and the PMID of the report.

Two caveats travel with the data. They are solved cases, so recall measured
here is an upper bound on recall in an undiagnosed clinic. And every case names
its source paper, and that paper is often among the sources HPO curated the
disease's annotations from — the very knowledge a phenotype tool matches
against. Anything that reads the literature or those annotations must be
stopped from reading the case's own paper; the split below and the masking in
raredx.knowledge exist for that.

Source and pinned release: the `phenopacket-store` entry in evals/datasets.toml.
"""

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from raredx.data.cases import Case, Split, Variant

ARCHIVE = "all_phenopackets.zip"  # the release file this parser reads

# ── the design / held-out split, decided by code, not by memory ─────
#
# Split by PMID, not by case: two individuals from one report share the
# authors' phrasing and often a pedigree, so putting one on each side would let
# the held-out half be solved by having seen its sibling. Half the PMIDs go
# each way, by a hash, so the assignment is fixed forever and nobody chooses.


def split_of(pmid: str) -> Split:
    h = int(hashlib.sha256(pmid.encode()).hexdigest(), 16)
    return "design" if h % 2 else "heldout"


# ── loading ─────────────────────────────────────────────────────────


def _first_pmid(packet: dict[str, Any]) -> str | None:
    for ref in (packet.get("metaData") or {}).get("externalReferences", []):
        ref_id = str(ref.get("id", ""))
        if ref_id.startswith("PMID:"):
            return ref_id
    return None


def _variants(diagnosis: dict[str, Any]) -> list[Variant]:
    out: list[Variant] = []
    for gi in diagnosis.get("genomicInterpretations", []):
        vd = (gi.get("variantInterpretation") or {}).get("variationDescriptor") or {}
        gene = (vd.get("geneContext") or {}).get("symbol")
        if not gene:
            continue
        hgvs = {e.get("syntax"): e.get("value") for e in vd.get("expressions", [])}
        out.append(
            Variant(
                gene=gene,
                hgvs_c=hgvs.get("hgvs.c"),
                hgvs_p=hgvs.get("hgvs.p"),
                zygosity=str((vd.get("allelicState") or {}).get("label") or "unknown").lower(),
            )
        )
    return out


def parse(packet: dict[str, Any], cohort: str) -> Case | str:
    """One phenopacket to one Case, or the reason it cannot be one."""
    present = [f for f in packet.get("phenotypicFeatures", []) if not f.get("excluded")]
    if not present:
        return "no_phenotype"
    interpretations = packet.get("interpretations") or []
    if not interpretations:
        return "no_diagnosis"
    diagnosis = interpretations[0].get("diagnosis") or {}
    disease = diagnosis.get("disease") or {}
    if not disease.get("id"):
        return "no_diagnosis"
    pmid = _first_pmid(packet)
    if pmid is None:
        return "no_pmid"
    variants = _variants(diagnosis)
    return Case(
        id=str(packet.get("id")),
        cohort=cohort,
        hpo_ids=[f["type"]["id"] for f in present],
        hpo_labels=[f["type"].get("label", "") for f in present],
        disease_id=disease["id"],
        disease_label=disease.get("label", ""),
        gene=variants[0].gene if variants else None,
        variants=variants,
        pmid=pmid,
        sex=(packet.get("subject") or {}).get("sex"),
        split=split_of(pmid),
    )


def load(archive: Path) -> tuple[list[Case], Counter[str]]:
    """Every usable case in the archive, plus a count of why the others were skipped."""
    cases: list[Case] = []
    skipped: Counter[str] = Counter()
    with zipfile.ZipFile(archive) as z:
        for name in sorted(z.namelist()):
            if not name.endswith(".json"):
                continue
            # layout: <version>/<cohort>/<file>.json
            cohort = name.split("/")[1] if name.count("/") >= 2 else ""
            try:
                packet = json.loads(z.read(name))
            except ValueError:
                skipped["unreadable"] += 1
                continue
            result = parse(packet, cohort)
            if isinstance(result, str):
                skipped[result] += 1
            else:
                cases.append(result)
    return cases, skipped


def design(cases: list[Case]) -> list[Case]:
    """The half everything is developed against."""
    return [c for c in cases if c.split == "design"]


def heldout(cases: list[Case]) -> list[Case]:
    """The half nothing may be developed against. Used once, when a design is final."""
    return [c for c in cases if c.split == "heldout"]

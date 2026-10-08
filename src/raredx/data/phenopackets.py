"""Phenopacket Store: published, solved rare-disease cases, used as the evaluation set.

Each phenopacket is one patient from one published report: the HPO terms the
authors observed, the OMIM disease the case was solved as, the causal gene and
variants, and the PMID of the report. Phenotype and diagnosis were recorded
independently of the gene-to-phenotype annotations a tool would use to match
them, which is what makes these cases usable as a benchmark.

Two caveats travel with the data. They are solved cases, so recall measured
here is an upper bound on recall in an undiagnosed clinic. And every case names
its source paper, so anything that reads the literature must be stopped from
reading that paper; the split below and the leakage controls in the eval layer
exist for that.

Source: https://github.com/monarch-initiative/phenopacket-store (releases).
"""

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel

RELEASE_VERSION = "0.1.27"
RELEASE_URL = (
    "https://github.com/monarch-initiative/phenopacket-store/releases/download/"
    f"{RELEASE_VERSION}/all_phenopackets.zip"
)
# sha256 of the release asset. A download that does not match is deleted, not used.
RELEASE_SHA256 = "d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a"

Split = Literal["design", "heldout"]


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
    disease_id: str  # OMIM:nnnnnn
    disease_label: str
    gene: str | None  # None for e.g. chromosomal-deletion cohorts
    variants: list[Variant]
    pmid: str  # PMID:nnnnnnnn — also decides the split
    sex: str | None
    split: Split


# ── fetching ────────────────────────────────────────────────────────


def archive_path(data_dir: Path) -> Path:
    return data_dir / "raw" / "phenopacket-store" / RELEASE_VERSION / "all_phenopackets.zip"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, expected: str) -> None:
    actual = sha256_of(path)
    if actual != expected:
        raise ValueError(f"{path}: sha256 {actual} != expected {expected}")


def fetch(data_dir: Path, *, force: bool = False) -> Path:
    """Download the release archive into data_dir and verify it. Idempotent."""
    target = archive_path(data_dir)
    if target.exists() and not force:
        verify(target, RELEASE_SHA256)
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".zip.part")
    with httpx.stream("GET", RELEASE_URL, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    try:
        verify(tmp, RELEASE_SHA256)
    except ValueError:
        tmp.unlink()
        raise
    tmp.replace(target)
    return target


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

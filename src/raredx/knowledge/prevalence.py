"""How rare each disease is: Orphanet's prevalence classes, mapped to OMIM.

For splitting results by rarity — "relatively common" rare diseases apart from
those known from a handful of families. No tool reads this.

A disorder's class is Orphanet's validated point prevalence, worldwide if it
gives one, else for any region; failing that, its prevalence at birth, then its
lifetime prevalence, then its annual incidence. A disorder Orphanet knows only by
counting the published cases or families is under one in a million. An OMIM
disease takes the class of the Orphanet disorders mapped to it exactly (the same
mapping the disease texts use); if those disagree, the most common class, so a
disease is never made rarer than Orphanet says.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Literal

PREVALENCE = "en_product9_prev.xml"

Band = Literal["1 in 100,000 or more", "1–9 in 1,000,000", "under 1 in 1,000,000", "unknown"]
BANDS: tuple[Band, ...] = (
    "1 in 100,000 or more",
    "1–9 in 1,000,000",
    "under 1 in 1,000,000",
    "unknown",
)
_BAND_OF_CLASS: dict[str, Band] = {
    ">1 / 1000": "1 in 100,000 or more",
    "6-9 / 10 000": "1 in 100,000 or more",
    "1-5 / 10 000": "1 in 100,000 or more",
    "1-9 / 100 000": "1 in 100,000 or more",
    "1-9 / 1 000 000": "1–9 in 1,000,000",
    "<1 / 1 000 000": "under 1 in 1,000,000",
}
# Orphanet's measures, in the order they are preferred (the names as the file writes them)
_TYPES = ("Point prevalence", "Prevalence at birth", "Lifetime Prevalence", "Annual incidence")
EXACT = "E ("  # Orphanet's mapping relation: "E (Exact mapping: the two concepts are equivalent)"


def bands(path: Path) -> dict[str, Band]:
    """Each Orphanet disorder's band, by ORPHA code ("ORPHA:166024")."""
    found: dict[str, Band] = {}
    for disorder in ET.parse(path).getroot().iter("Disorder"):
        ranked: list[tuple[int, int, Band]] = []
        case_reports = False
        for p in disorder.iter("Prevalence"):
            if p.findtext("PrevalenceValidationStatus/Name") != "Validated":
                continue
            kind = p.findtext("PrevalenceType/Name") or ""
            band = _BAND_OF_CLASS.get(p.findtext("PrevalenceClass/Name") or "")
            if kind == "Cases/families":
                case_reports = True
            elif kind in _TYPES and band is not None:
                worldwide = p.findtext("PrevalenceGeographic/Name") == "Worldwide"
                ranked.append((_TYPES.index(kind), 0 if worldwide else 1, band))
        if ranked:
            found[f"ORPHA:{disorder.findtext('OrphaCode')}"] = min(ranked)[2]
        elif case_reports:
            found[f"ORPHA:{disorder.findtext('OrphaCode')}"] = "under 1 in 1,000,000"
    return found


def omim_mapping(path: Path) -> dict[str, set[str]]:
    """The Orphanet disorders mapped exactly to each OMIM disease, from Orphanet's
    disorder file (en_product1.xml)."""
    mapped: dict[str, set[str]] = defaultdict(set)
    for disorder in ET.parse(path).getroot().iter("Disorder"):
        orpha = f"ORPHA:{disorder.findtext('OrphaCode')}"
        for ref in disorder.iter("ExternalReference"):
            relation = ref.findtext("DisorderMappingRelation/Name") or ""
            if ref.findtext("Source") == "OMIM" and relation.startswith(EXACT):
                mapped[f"OMIM:{ref.findtext('Reference')}"].add(orpha)
    return dict(mapped)


def omim_bands(prevalence: Path, disorders: Path) -> dict[str, Band]:
    """Each OMIM disease's band; a disease absent here is of unknown prevalence."""
    of_orpha = bands(prevalence)
    out: dict[str, Band] = {}
    for omim, orphas in omim_mapping(disorders).items():
        known = [of_orpha[o] for o in orphas if o in of_orpha]
        if known:
            out[omim] = min(known, key=BANDS.index)  # the most common
    return out

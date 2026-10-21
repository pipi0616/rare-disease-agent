"""How rare each disease is: Orphanet's prevalence classes, mapped to OMIM.

For splitting results by rarity — "relatively common" rare diseases apart from
those known from a handful of families — in bands; and, as Orphanet writes the
class ("1-5 / 10 000"), for the hypothesis agent to weigh how common a candidate
is. No tool reads this.

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
# Orphanet's classes, most common first
CLASSES = tuple(_BAND_OF_CLASS)
CASE_REPORTS = "<1 / 1 000 000"  # a disorder known only by counting its published cases
# Orphanet's measures, in the order they are preferred (the names as the file writes them)
_TYPES = ("Point prevalence", "Prevalence at birth", "Lifetime Prevalence", "Annual incidence")
EXACT = "E ("  # Orphanet's mapping relation: "E (Exact mapping: the two concepts are equivalent)"


def classes(path: Path) -> dict[str, str]:
    """Each Orphanet disorder's class as Orphanet writes it, by ORPHA code ("ORPHA:166024")."""
    found: dict[str, str] = {}
    for disorder in ET.parse(path).getroot().iter("Disorder"):
        ranked: list[tuple[int, int, int]] = []
        case_reports = False
        for p in disorder.iter("Prevalence"):
            if p.findtext("PrevalenceValidationStatus/Name") != "Validated":
                continue
            kind = p.findtext("PrevalenceType/Name") or ""
            cls = p.findtext("PrevalenceClass/Name") or ""
            if kind == "Cases/families":
                case_reports = True
            elif kind in _TYPES and cls in CLASSES:
                worldwide = p.findtext("PrevalenceGeographic/Name") == "Worldwide"
                ranked.append((_TYPES.index(kind), 0 if worldwide else 1, CLASSES.index(cls)))
        if ranked:
            found[f"ORPHA:{disorder.findtext('OrphaCode')}"] = CLASSES[min(ranked)[2]]
        elif case_reports:
            found[f"ORPHA:{disorder.findtext('OrphaCode')}"] = CASE_REPORTS
    return found


def bands(path: Path) -> dict[str, Band]:
    """Each Orphanet disorder's band, by ORPHA code."""
    return {code: _BAND_OF_CLASS[cls] for code, cls in classes(path).items()}


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


def omim_classes(prevalence: Path, disorders: Path) -> dict[str, str]:
    """Each OMIM disease's class; a disease absent here is of unknown prevalence."""
    of_orpha = classes(prevalence)
    out: dict[str, str] = {}
    for omim, orphas in omim_mapping(disorders).items():
        known = [of_orpha[o] for o in orphas if o in of_orpha]
        if known:
            out[omim] = min(known, key=CLASSES.index)  # the most common
    return out


def omim_bands(prevalence: Path, disorders: Path) -> dict[str, Band]:
    """Each OMIM disease's band; a disease absent here is of unknown prevalence."""
    return {omim: _BAND_OF_CLASS[cls] for omim, cls in omim_classes(prevalence, disorders).items()}

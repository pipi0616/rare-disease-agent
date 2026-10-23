"""Disease texts: what Orphanet and MedlinePlus Genetics write about each disease.

The phenotype tools read HPO's structured annotations. These are the prose
descriptions clinicians read, cut into passages for retrieval:

- Orphanet (CC BY 4.0): one definition per rare disease, about fifty words.
  A disorder is linked to the OMIM entries Orphanet maps to it exactly.
- MedlinePlus Genetics (public domain, NLM): a description of each genetic
  condition, several paragraphs long; one passage per paragraph, each led by
  the condition's name. A condition is linked to every OMIM entry it lists.

Only passages linked to at least one OMIM disease are kept: OMIM ids are what
the other tools and the scorer speak. Neither source cites its papers, so a
passage cannot be masked by reference; the tool hides the diseases known only
from a masked paper instead (see search_disease_texts).
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from pydantic import BaseModel

ORPHANET = "en_product1.xml"
MEDLINEPLUS = "ghr-summaries.xml"
_MEDLINEPLUS_NS = "https://medlineplus.gov/download/ghr-summaries-20250602.xsd"
_XHTML = "{http://www.w3.org/1999/xhtml}"
_TAG = re.compile(r"<[^>]+>")
EXACT = "E "  # Orphanet's mapping relation "E (Exact mapping: the two concepts are equivalent)"


class Passage(BaseModel):
    text: str  # led by the disease's name, as it is embedded and shown
    disease_ids: list[str]  # the OMIM diseases it is about
    disease_name: str
    source: str  # e.g. "Orphanet ORPHA:166024", or the MedlinePlus page
    # Chapter 33's corpus also records, per chunk: its document, its section, the papers
    # its paragraphs cite (for masking by reference), and, when what is searched is a
    # small piece, the larger text returned in its place.
    doc: str = ""
    section: str = ""
    pmids: list[str] = []
    parent: str = ""


def orphanet(path: Path) -> list[Passage]:
    """Orphanet's definitions of disorders mapped exactly to OMIM."""
    passages = []
    for disorder in ET.parse(path).getroot().iter("Disorder"):
        omim = sorted(
            {
                f"OMIM:{ref.findtext('Reference')}"
                for ref in disorder.iter("ExternalReference")
                if ref.findtext("Source") == "OMIM"
                and (ref.findtext("DisorderMappingRelation/Name") or "").startswith(EXACT)
            }
        )
        definition = next(
            (
                "".join(contents.itertext())  # markup comes escaped, or, in places, as elements
                for section in disorder.iter("TextSection")
                if section.findtext("TextSectionType/Name") == "Definition"
                and (contents := section.find("Contents")) is not None
            ),
            None,
        )
        if omim and definition:
            name = disorder.findtext("Name") or ""
            passages.append(
                Passage(
                    text=f"{name}. {_TAG.sub('', definition).strip()}",
                    disease_ids=omim,
                    disease_name=name,
                    source=f"Orphanet ORPHA:{disorder.findtext('OrphaCode')}",
                )
            )
    return passages


def medlineplus(path: Path) -> list[Passage]:
    """MedlinePlus Genetics condition descriptions, one passage per paragraph."""
    ns = {"m": _MEDLINEPLUS_NS}
    passages = []
    for condition in ET.parse(path).getroot().findall("m:health-condition-summary", ns):
        omim = sorted(
            {
                f"OMIM:{key.findtext('m:key', namespaces=ns)}"
                for key in condition.findall(".//m:db-key", ns)
                if key.findtext("m:db", namespaces=ns) == "OMIM"
            }
        )
        if not omim:
            continue
        name = condition.findtext("m:name", namespaces=ns) or ""
        page = condition.findtext("m:ghr-page", namespaces=ns) or ""
        for text in condition.findall("m:text-list/m:text", ns):
            if text.findtext("m:text-role", namespaces=ns) != "description":
                continue
            for paragraph in text.iter(f"{_XHTML}p"):
                body = "".join(paragraph.itertext()).strip()
                if body:
                    passages.append(
                        Passage(
                            text=f"{name}. {body}",
                            disease_ids=omim,
                            disease_name=name,
                            source=page,
                        )
                    )
    return passages


def read(orphanet_dir: Path, medlineplus_dir: Path) -> list[Passage]:
    """Both sources' passages, Orphanet first, each in its file's order."""
    return orphanet(orphanet_dir / ORPHANET) + medlineplus(medlineplus_dir / MEDLINEPLUS)

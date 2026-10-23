"""The disease corpus: every text the RAG tool can read, as structured documents.

Chapter 18 read two sources, each cut into passages as it was read. This reads five,
into one shape — a document about some diseases, in sections of paragraphs, each
paragraph with the papers it cites — so that how documents are cut into chunks is a
separate step (raredx.knowledge.chunking) and can be compared.

| source       | what                                     | cites papers | licence            |
|--------------|------------------------------------------|--------------|--------------------|
| GeneReviews  | ~900 chapters: diagnosis, clinical       | per paragraph| non-commercial     |
|              | description, differential, counselling   |              | research only      |
| Wikipedia    | articles on the knowledge's diseases     | per paragraph| CC BY-SA 4.0       |
| Orphanet     | one definition per disorder              | no           | CC BY 4.0          |
| Mondo        | one definition per disease class         | some         | CC BY 4.0          |
| MedlinePlus  | genetic-condition summaries              | no           | public domain      |

Cited papers are what masking by reference needs: in evaluation, a paragraph citing
the case's own paper is hidden, as an HPO annotation citing it is.

A document names diseases by the ids its source uses (OMIM, ORPHA); `resolve` maps
them to the knowledge's diseases and drops documents about none.
"""

import re
import tarfile
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from pathlib import Path

from pydantic import BaseModel

from raredx.knowledge.hpo import HPO

_SPACE = re.compile(r"\s+")
_PUBMED = re.compile(r"(?:pubmed\.ncbi\.nlm\.nih\.gov/|ncbi\.nlm\.nih\.gov/pubmed/)(\d+)")


class Paragraph(BaseModel):
    text: str
    pmids: list[str] = []  # "PMID:n", the papers it cites


class Section(BaseModel):
    title: str = ""  # "" for a document of one section
    paragraphs: list[Paragraph]


class Document(BaseModel):
    id: str  # unique across sources, e.g. "GeneReviews:pku"
    source: str
    title: str
    disease_ids: list[str]
    sections: list[Section]
    url: str = ""

    def words(self) -> int:
        return sum(len(p.text.split()) for s in self.sections for p in s.paragraphs)


def _clean(text: str) -> str:
    return _SPACE.sub(" ", text).strip()


def _title(element: ET.Element) -> str:
    """An element's <title>, as text ("" if none). (An element without children is
    falsy, so `find(...) or default` would lose it.)"""
    title = element.find("title")
    return _clean("".join(title.itertext())) if title is not None else ""


# ---------------------------------------------------------------- GeneReviews

GENEREVIEWS_BOOK = "gene_NBK1116.tar.gz"
GENEREVIEWS_OMIM = "NBKid_shortname_OMIM.txt"
GENEREVIEWS_URL = "https://www.ncbi.nlm.nih.gov/books/"
# What is left out: treatment, variants, and the chapter's apparatus. Kept: the
# summary, diagnosis, clinical characteristics, related disorders, differential
# diagnosis, genetic counselling.
GENEREVIEWS_SKIP = (
    "Management",
    "Molecular Genetics",
    "References",
    "Resources",
    "Chapter Notes",
    "Key Sections",
    "Tests in GTR",
)


def _genereviews_omim(path: Path) -> dict[str, tuple[str, list[str]]]:
    """GeneReviews short name -> its NBK id and the OMIM ids NCBI links the chapter to."""
    out: dict[str, tuple[str, list[str]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        nbk, short, omim = line.split("\t")[:3]
        if omim.strip().isdigit():
            out.setdefault(short, (nbk, []))[1].append(f"OMIM:{omim.strip()}")
    return out


def _gr_paragraphs(element: ET.Element, refs: dict[str, str]) -> Iterator[Paragraph]:
    """The paragraphs directly in a section, in order: <p>, and each list item; tables
    are left out."""
    for child in element:
        if child.tag == "p":
            yield _gr_paragraph(child, refs)
        elif child.tag == "list":
            for item in child.iter("list-item"):
                yield _gr_paragraph(item, refs)


def _gr_paragraph(element: ET.Element, refs: dict[str, str]) -> Paragraph:
    cited = {
        refs[rid]
        for x in element.iter("xref")
        if x.get("ref-type") == "bibr"
        for rid in (x.get("rid") or "").split()
        if rid in refs
    }
    return Paragraph(text=_clean("".join(element.itertext())), pmids=sorted(cited))


def _gr_sections(sec: ET.Element, path: str, refs: dict[str, str]) -> Iterator[Section]:
    title = _title(sec)
    if title.startswith(GENEREVIEWS_SKIP):
        return
    here = f"{path} — {title}" if path and title else (title or path)
    paragraphs = [p for p in _gr_paragraphs(sec, refs) if p.text]
    if paragraphs:
        yield Section(title=here, paragraphs=paragraphs)
    for sub in sec.findall("sec"):
        yield from _gr_sections(sub, here, refs)


def genereviews_chapter(xml: bytes, short: str, nbk: str, omim: list[str]) -> Document | None:
    root = ET.fromstring(xml)
    part = root.find("book-part")
    if part is None:
        return None
    meta = part.find("book-part-meta")
    group = meta.find("title-group") if meta is not None else None
    title = _title(group) if group is not None else short
    refs = {
        ref.get("id", ""): f"PMID:{pmid.text.strip()}"
        for ref in root.iter("ref")
        if (pmid := ref.find(".//pub-id[@pub-id-type='pmid']")) is not None and pmid.text
    }
    sections: list[Section] = []
    abstract = meta.find("abstract") if meta is not None else None
    if abstract is not None:
        for sec in abstract.findall("sec") or [abstract]:
            sections.extend(_gr_sections(sec, "Summary", refs))
    body = part.find("body")
    for sec in body.findall("sec") if body is not None else []:
        sections.extend(_gr_sections(sec, "", refs))
    if not sections:
        return None
    return Document(
        id=f"GeneReviews:{short}",
        source="genereviews",
        title=title,
        disease_ids=omim,
        sections=sections,
        url=GENEREVIEWS_URL + nbk,
    )


def genereviews(book: Path, omim_table: Path) -> Iterator[Document]:
    """Every GeneReviews chapter NCBI links to an OMIM disease."""
    omim = _genereviews_omim(omim_table)
    with tarfile.open(book) as tar:
        for member in tar:
            if not member.name.endswith(".nxml"):
                continue
            short = Path(member.name).stem
            if short not in omim:
                continue
            f = tar.extractfile(member)
            if f is None:
                continue
            doc = genereviews_chapter(f.read(), short, *omim[short])
            if doc:
                yield doc


# ---------------------------------------------------------------- Wikipedia

WIKIPEDIA_SKIP = {
    "References",
    "External links",
    "See also",
    "Further reading",
    "Notes",
    "Bibliography",
    "Sources",
    "Citations",
    "Footnotes",
}


def wikipedia_article(page: dict[str, object]) -> Document | None:
    """An article's sections and paragraphs from its HTML, with the PubMed ids each
    paragraph's footnotes point to; infoboxes, tables, figures and navigation left out."""
    from bs4 import BeautifulSoup, Tag

    soup = BeautifulSoup(str(page["html"]), "html.parser")
    root = soup.select_one("div.mw-parser-output") or soup
    notes: dict[str, list[str]] = {}
    for li in root.select("ol.references > li[id]"):
        links = " ".join(str(a.get("href") or "") for a in li.find_all("a"))
        notes[str(li["id"])] = sorted({f"PMID:{n}" for n in _PUBMED.findall(links)})
    sections: list[Section] = []
    current = Section(title="", paragraphs=[])
    skipping = False

    def paragraph(tag: "Tag") -> Paragraph | None:
        cited: set[str] = set()
        for sup in tag.select("sup.reference"):
            a = sup.find("a")
            if a and str(a.get("href", "")).startswith("#"):
                cited.update(notes.get(str(a["href"])[1:], []))
            sup.decompose()
        text = _clean(tag.get_text(" "))
        return Paragraph(text=text, pmids=sorted(cited)) if len(text.split()) >= 3 else None

    for child in root.find_all(recursive=False):
        classes: list[str] = list(child.get("class") or [])
        heading = child.find(["h2", "h3"]) if "mw-heading" in classes else None
        if heading is not None or child.name in ("h2", "h3"):
            title = _clean((heading or child).get_text(" "))
            if current.paragraphs:
                sections.append(current)
            level2 = "mw-heading2" in classes or child.name == "h2"
            if level2:
                skipping = title in WIKIPEDIA_SKIP
            current = Section(title=title, paragraphs=[])
            continue
        if skipping:
            continue
        if child.name == "p":
            if p := paragraph(child):
                current.paragraphs.append(p)
        elif child.name in ("ul", "ol") and not ({"references", "gallery"} & set(classes)):
            for li in child.find_all("li", recursive=False):
                if p := paragraph(li):
                    current.paragraphs.append(p)
    if current.paragraphs:
        sections.append(current)
    if not sections:
        return None
    title = str(page["title"])
    ids = [*map(str, page["orpha"]), *map(str, page["omim"])]  # type: ignore[call-overload]
    return Document(
        id=f"Wikipedia:{title}",
        source="wikipedia",
        title=title,
        disease_ids=ids,
        sections=sections,
        url=f"https://en.wikipedia.org/w/index.php?oldid={page['revid']}",
    )


def wikipedia(
    pages: Iterable[dict[str, object]], diseases: dict[int, list[str]] | None = None
) -> Iterator[Document]:
    """The fetched articles; their diseases from the manifest (diseases, by revision)
    when given, where titles sharing an article are merged."""
    seen: set[str] = set()
    for page in pages:
        if str(page["revid"]) in seen:  # fetched twice
            continue
        seen.add(str(page["revid"]))
        if diseases and int(str(page["revid"])) in diseases:
            page = {**page, "orpha": [], "omim": diseases[int(str(page["revid"]))]}
        if doc := wikipedia_article(page):
            yield doc


# ---------------------------------------------------------------- Orphanet

ORPHANET = "en_product1.xml"


def orphanet(path: Path) -> Iterator[Document]:
    """Every Orphanet disorder's definition, the disorder named by its ORPHA code."""
    for disorder in ET.parse(path).getroot().iter("Disorder"):
        definition = next(
            (
                "".join(contents.itertext())
                for section in disorder.iter("TextSection")
                if section.findtext("TextSectionType/Name") == "Definition"
                and (contents := section.find("Contents")) is not None
            ),
            None,
        )
        code = disorder.findtext("OrphaCode")
        if definition and code:
            yield Document(
                id=f"Orphanet:ORPHA:{code}",
                source="orphanet",
                title=disorder.findtext("Name") or "",
                disease_ids=[f"ORPHA:{code}"],
                sections=[Section(paragraphs=[Paragraph(text=_clean(definition))])],
                url=f"https://www.orpha.net/en/disease/detail/{code}",
            )


# ---------------------------------------------------------------- Mondo

MONDO = "mondo.obo"
_DEF = re.compile(r'^def: "(.*)" \[(.*)\]')


def mondo(path: Path, members: dict[str, frozenset[str]]) -> Iterator[Document]:
    """Each Mondo class's definition, about the OMIM and ORPHA ids it matches exactly
    (members); classes matching none are left out."""
    term: dict[str, str] = {}

    def done() -> Document | None:
        ids = members.get(term.get("id", ""))
        if not ids or "def" not in term:
            return None
        cited = sorted(set(re.findall(r"PMID:\d+", term.get("xrefs", ""))))
        return Document(
            id=f"Mondo:{term['id']}",
            source="mondo",
            title=term.get("name", ""),
            disease_ids=sorted(ids),
            sections=[Section(paragraphs=[Paragraph(text=term["def"], pmids=cited)])],
            url=f"https://monarchinitiative.org/{term['id']}",
        )

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("["):
                if doc := done():
                    yield doc
                term = {}
            elif line.startswith("id: "):
                term["id"] = line[4:]
            elif line.startswith("name: "):
                term["name"] = line[6:]
            elif m := _DEF.match(line):
                term["def"] = m.group(1).replace('\\"', '"')
                term["xrefs"] = m.group(2)
        if doc := done():
            yield doc


# ---------------------------------------------------------------- MedlinePlus

MEDLINEPLUS = "ghr-summaries.xml"
_MEDLINEPLUS_NS = "https://medlineplus.gov/download/ghr-summaries-20250602.xsd"
_XHTML = "{http://www.w3.org/1999/xhtml}"


def medlineplus(path: Path) -> Iterator[Document]:
    """Each MedlinePlus Genetics condition's description, one paragraph per paragraph."""
    ns = {"m": _MEDLINEPLUS_NS}
    for condition in ET.parse(path).getroot().findall("m:health-condition-summary", ns):
        omim = sorted(
            {
                f"OMIM:{key.findtext('m:key', namespaces=ns)}"
                for key in condition.findall(".//m:db-key", ns)
                if key.findtext("m:db", namespaces=ns) == "OMIM"
            }
        )
        paragraphs = [
            Paragraph(text=_clean("".join(p.itertext())))
            for text in condition.findall("m:text-list/m:text", ns)
            if text.findtext("m:text-role", namespaces=ns) == "description"
            for p in text.iter(f"{_XHTML}p")
            if "".join(p.itertext()).strip()
        ]
        page = condition.findtext("m:ghr-page", namespaces=ns) or ""
        if omim and paragraphs:
            yield Document(
                id=f"MedlinePlus:{page.rstrip('/').rsplit('/', 1)[-1]}",
                source="medlineplus",
                title=condition.findtext("m:name", namespaces=ns) or "",
                disease_ids=omim,
                sections=[Section(paragraphs=paragraphs)],
                url=page,
            )


# ---------------------------------------------------------------- all together


def resolve(documents: Iterable[Document], hpo: HPO) -> Iterator[Document]:
    """The documents with their diseases named as the knowledge names them; those
    about no disease of the knowledge are dropped."""
    for doc in documents:
        known = sorted({c for d in doc.disease_ids if (c := hpo.canonical(d))})
        if known:
            yield doc.model_copy(update={"disease_ids": known})

"""Case reports first public after the model's training cutoff, as test and development
cases: which papers, what each one's diagnosis is, and where its case description is cut
so that what is left does not give the diagnosis away (docs/casereports_plan.md).

    candidates   PubMed: case reports in English with open-access full text in PMC,
                 entered in a date range; put in one fixed random order (SEED)
    annotator A  PubTator3 (NCBI): the diseases named in the title and the abstract, as
                 MeSH ids; through Mondo, the diseases of the knowledge they are
    full text    NCBI's BioC service: the paragraphs of the case description (CASE)
    annotator B  the model, temperature 0: the final diagnosis as the authors name it,
                 how many patients, whether the report goes from presentation to
                 diagnosis, and the first sentence that gives the diagnosis away
    answer key   kept only where the two agree: B's diagnosis, found by name, is the one
                 disease of the knowledge A found in the title. Anything else is skipped
                 and logged — no one adjudicates
    the cut      everything from the first revealing sentence on is dropped: B's
                 sentence, or the first one a program finds the disease's name, a synonym
                 or its gene in, whichever is earlier. Nothing is rewritten
    the sides    each disease belongs to the test or to development by a fixed draw made
                 before any paper is read, so no disease is on both sides

A paper is processed in the fixed order until both sides are full; which papers are used
is decided by the order, not chosen. Texts stay on this machine (some licences are
non-commercial); the table in git names each paper, its cut and the checksum of what
was kept, so anyone can rebuild them.
"""

import hashlib
import json
import math
import random
import re
import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from raredx.knowledge.diseases import EXACT, Identity

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBTATOR = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson"
BIOC = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmid}/unicode"
QUERY = (
    '"Case Reports"[pt] AND english[la] AND "pubmed pmc open access"[filter] '
    'AND ("{first}"[edat] : "{last}"[edat])'
)
NAME = "casereports-2026-10"
VERSION = "2026-10"
TEXTS = "texts.jsonl"  # the kept texts: local only, pinned by checksum in the registry
START, END = date(2025, 6, 1), date(2026, 10, 24)  # entered PubMed in this range
PILOT = (date(2025, 3, 1), date(2025, 3, 7))  # before the cutoff: for debugging only
SEED = 20261025
EXAM_SIZE, DEV_SIZE = 240, 300
PER_DISEASE = 3
COMMON = "1 in 100,000 or more"  # the prevalence band at least a third of each side has
COMMON_SHARE = 1 / 3
MIN_WORDS = 60
SEARCH_LIMIT = 9_999  # PubMed returns no more ids than this for one query
ANNOTATE_BATCH = 100
PROMPT_VERSION = "casereport-key-v2"  # v2: the disease name alone (after the pilot)


# ── candidates ──────────────────────────────────────────────────────


def _window(first: date, last: date, http: httpx.Client, pause: float) -> set[str]:
    term = QUERY.format(first=first.strftime("%Y/%m/%d"), last=last.strftime("%Y/%m/%d"))
    params = {"db": "pubmed", "retmode": "json", "retmax": str(SEARCH_LIMIT), "term": term}
    response = http.get(ESEARCH, params=params)
    response.raise_for_status()
    result = response.json()["esearchresult"]
    time.sleep(pause)
    if int(result["count"]) > SEARCH_LIMIT and last > first:  # too many for one query: halve
        middle = first + (last - first) // 2
        return _window(first, middle, http, pause) | _window(
            middle + timedelta(days=1), last, http, pause
        )
    return set(result["idlist"])


def search(first: date, last: date, http: httpx.Client, pause: float = 0.4) -> list[str]:
    """The PMIDs (numbers) of every candidate entered between the two days, sorted."""
    found: set[str] = set()
    day = first
    while day <= last:
        until = min(day + timedelta(days=6), last)
        found |= _window(day, until, http, pause)
        day = until + timedelta(days=1)
    return sorted(found, key=int)


def ordered(pmids: Iterable[str], seed: int = SEED) -> list[str]:
    """The candidates in the one order they are processed in."""
    order = sorted(set(pmids), key=int)
    random.Random(seed).shuffle(order)
    return order


# ── annotator A: PubTator3 ──────────────────────────────────────────


class Abstract(BaseModel):
    pmid: str
    title: str
    abstract: str
    title_diseases: list[str]  # identifiers as PubTator3 gives them, e.g. MESH:D008382
    abstract_diseases: list[str]


def read_annotations(payload: Any) -> list[Abstract]:
    """PubTator3's BioC JSON as one Abstract per paper."""
    out = []
    for doc in payload.get("PubTator3", []) if isinstance(payload, dict) else []:
        text = {"title": "", "abstract": ""}
        found: dict[str, list[str]] = {"title": [], "abstract": []}
        for passage in doc.get("passages", []):
            where = passage.get("infons", {}).get("type")
            if where not in text:
                continue
            text[where] = (text[where] + " " + passage.get("text", "")).strip()
            for annotation in passage.get("annotations", []):
                infons = annotation.get("infons", {})
                identifier = infons.get("identifier")
                is_disease = infons.get("type") == "Disease"
                if is_disease and identifier and identifier not in found[where]:
                    found[where].append(identifier)
        out.append(
            Abstract(
                pmid=str(doc.get("pmid") or doc.get("id")),
                title=text["title"],
                abstract=text["abstract"],
                title_diseases=found["title"],
                abstract_diseases=found["abstract"],
            )
        )
    return out


def annotate(pmids: list[str], http: httpx.Client, pause: float = 0.4) -> list[Abstract]:
    """Annotator A on a batch of papers (at most ANNOTATE_BATCH)."""
    response = http.get(PUBTATOR, params={"pmids": ",".join(pmids)})
    response.raise_for_status()
    time.sleep(pause)
    return read_annotations(response.json())


class Mesh:
    """MeSH ids as Mondo classes, by Mondo's exact matches; and each class's OMIM and
    ORPHA ids. An OMIM id PubTator3 gives directly is read too."""

    def __init__(self, mappings: Path, identity: Identity) -> None:
        self._identity = identity
        self._class: dict[str, str] = {}
        with mappings.open(encoding="utf-8") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                subject, _, predicate, target = line.split("\t", 4)[:4]
                if predicate == EXACT and target.lower().startswith("mesh:"):
                    self._class[target.split(":", 1)[1]] = subject
        self._members = identity.classes()

    def mondo(self, identifier: str) -> str | None:
        """The Mondo class of one of PubTator3's disease identifiers, if it has one."""
        prefix, _, local = identifier.partition(":")
        if prefix.upper() == "MESH":
            return self._class.get(local)
        if prefix.upper() == "OMIM":
            return self._identity.mondo(f"OMIM:{local}")
        return None

    def diseases(self, mondo: str) -> frozenset[str]:
        """The OMIM and ORPHA ids a Mondo class matches exactly."""
        return self._members.get(mondo, frozenset())


# ── the full text ───────────────────────────────────────────────────


class FullText(BaseModel):
    pmid: str
    pmcid: str | None
    license: str
    paragraphs: list[str]  # the case description, in order


def read_bioc(pmid: str, payload: Any) -> FullText | None:
    """The case description from BioC JSON: the paragraphs of the section typed CASE.
    Titles, tables and figure captions are not read."""
    collections = payload if isinstance(payload, list) else [payload]
    documents = collections[0].get("documents", []) if collections else []
    if not documents:
        return None
    passages = documents[0].get("passages", [])
    front = passages[0].get("infons", {}) if passages else {}
    paragraphs = [
        p["text"].strip()
        for p in passages
        if p.get("infons", {}).get("section_type") == "CASE"
        and p.get("infons", {}).get("type") == "paragraph"
        and p.get("text", "").strip()
    ]
    pmcid = front.get("article-id_pmc")
    return FullText(
        pmid=pmid,
        pmcid=f"PMC{pmcid}" if pmcid and not str(pmcid).startswith("PMC") else pmcid,
        license=str(front.get("license") or ""),
        paragraphs=paragraphs,
    )


def full_text(
    pmid: str, http: httpx.Client, pause: float = 1.1, waits: tuple[float, ...] = (5, 20, 60)
) -> FullText | None:
    """A paper's case description from the BioC service; None when the service says it
    has no such paper (it answers those with a page, not JSON, or with 404). The service
    allows about one request a second and refuses more (429): asked again after a wait,
    and a refusal that outlasts the waits is raised, not taken for a missing paper — a
    paper must not drop out of the build because the service was busy."""
    for wait in (*waits, None):
        response = http.get(BIOC.format(pmid=pmid))
        time.sleep(pause)
        if response.status_code == 200:
            try:
                return read_bioc(pmid, response.json())
            except (json.JSONDecodeError, KeyError, IndexError, AttributeError):
                return None
        if response.status_code == 404:
            return None
        if wait is None:
            response.raise_for_status()
            return None  # not reached for a refusal: raise_for_status raised
        time.sleep(wait)
    return None


# ── sentences ───────────────────────────────────────────────────────

_BREAK = re.compile(r"(?<=[.!?])[\"')\]]?\s+(?=[\"'(\[]?[A-Z0-9])")
_NOT_AN_END = re.compile(
    r"(?:\b(?:Dr|Mr|Mrs|Ms|Prof|Fig|Figs|No|vs|approx|ca|cf|Ref|Refs|Tab|Eq|St|al|etc|e\.g|i\.e)"
    r"|\b[A-Z])\.$"
)


def sentences(paragraphs: list[str]) -> list[str]:
    """The case description as sentences, by fixed rules: a paragraph ends a sentence;
    within one, a full stop, question or exclamation mark followed by space and a capital
    or a digit does — unless it ends a common abbreviation or a single capital letter."""
    out: list[str] = []
    for paragraph in paragraphs:
        pieces = _BREAK.split(re.sub(r"\s+", " ", paragraph).strip())
        held = ""
        for piece in pieces:
            held = f"{held} {piece}".strip() if held else piece
            if _NOT_AN_END.search(held):
                continue
            out.append(held)
            held = ""
        if held:
            out.append(held)
    return [s for s in out if s]


# ── annotator B: the model ──────────────────────────────────────────

B_SYSTEM = """\
You read one published case report and answer four questions about it. Reply with a \
json object and nothing else:

{"diagnosis": "...", "patients": 1, "diagnostic": true, "reveal": 7}

- "diagnosis": the patient's final diagnosis, the disease the report is about: the \
disease's name alone, as the authors write it in full — no site, cause, complication or \
circumstance around it, not an abbreviation alone, not a group of diseases when they \
give the specific one. If what looked like one disease turned out to be another thing \
(a foreign body, a drug reaction), name what it turned out to be.
- "patients": how many patients the report describes.
- "diagnostic": true if the case description begins before the diagnosis was known and \
tells how it was reached; false if the diagnosis is already known where the description \
begins (a report about treating or following a known disease).
- "reveal": the number of the first sentence of the case description that gives the \
diagnosis away, or null if none does. A sentence gives it away if it names the disease \
or a synonym, or says it is suspected or considered; names its causal gene or a variant; \
reports the result of a test that establishes it (genetic testing, histopathology, a \
specific enzyme or antibody assay); or names a treatment used only for this disease."""


class Key(BaseModel):
    """Annotator B's reading of one report."""

    diagnosis: str = Field(min_length=1)
    patients: int = Field(ge=0)
    diagnostic: bool
    reveal: int | None = None


def b_prompt(title: str, abstract: str, numbered: list[str]) -> str:
    lines = "\n".join(f"[{i}] {s}" for i, s in enumerate(numbered, 1))
    return (
        f"Title: {title}\n\nAbstract: {abstract}\n\n"
        f"Case description, one numbered sentence per line:\n{lines}"
    )


def parse_key(content: str | None) -> Key:
    return Key.model_validate_json(content or "")


# ── the cut ─────────────────────────────────────────────────────────

_PLAIN = re.compile(r"[^a-z0-9]+")


def name_forms(names: Iterable[str]) -> tuple[set[str], set[str]]:
    """What to look for in a sentence, from a disease's names and synonyms: (long forms,
    matched as whole words whatever the case and punctuation; short forms — an
    abbreviation such as MFS — matched as written). An OMIM title holds several forms
    between semicolons; a name's part before its first comma ("Ehlers-Danlos syndrome,
    classic type") is a form too when it is long enough to be specific."""
    long, short = set(), set()
    for name in names:
        for part in name.split(";"):
            part = part.strip().lstrip("#%+^*").strip()
            if not part:
                continue
            if len(part) <= 6 and part.upper() == part and " " not in part:
                if len(part) >= 3:
                    short.add(part)
                continue
            long.add(_PLAIN.sub(" ", part.lower()).strip())
            head = part.split(",")[0].strip()
            if len(head) >= 12 and " " in head:
                long.add(_PLAIN.sub(" ", head.lower()).strip())
    return {f for f in long if len(f) >= 5}, short


def reveals(sentence: str, long: set[str], short: set[str], genes: Iterable[str]) -> bool:
    """Whether a sentence names the disease (a long form, or an abbreviation as written)
    or one of its genes (as written, a whole word)."""
    plain = f" {_PLAIN.sub(' ', sentence.lower()).strip()} "
    if any(f" {form} " in plain for form in long):
        return True
    words = set(re.findall(r"[A-Za-z0-9-]+", sentence))
    return any(form in words for form in short) or any(gene in words for gene in genes)


def cut(
    numbered: list[str], reveal: int | None, long: set[str], short: set[str], genes: Iterable[str]
) -> int:
    """How many sentences are kept: those before the first revealing one — B's, or the
    first the program finds a name or gene in, whichever is earlier."""
    genes = list(genes)
    kept = len(numbered) if reveal is None else max(0, min(reveal - 1, len(numbered)))
    for i, sentence in enumerate(numbered[:kept]):
        if reveals(sentence, long, short, genes):
            return i
    return kept


def kept_text(numbered: list[str], kept: int) -> str:
    return " ".join(numbered[:kept])


def checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── the sides and their quotas ──────────────────────────────────────


def side_of(disease_class: str, seed: int = SEED) -> str:
    """The side a disease belongs to — "exam" or "dev" — by a draw that depends on the
    disease and the seed alone: fixed before any paper is read."""
    draw = random.Random(f"{seed}:{disease_class}").random()
    return "exam" if draw < EXAM_SIZE / (EXAM_SIZE + DEV_SIZE) else "dev"


class Selection:
    """What has been accepted so far, and whether one more case fits: at most PER_DISEASE
    per disease; each side up to its size, of which at least COMMON_SHARE are relatively
    common diseases — so the others stop at the rest."""

    def __init__(self, sizes: dict[str, int] | None = None) -> None:
        self.sizes = sizes or {"exam": EXAM_SIZE, "dev": DEV_SIZE}
        self.total: dict[str, int] = defaultdict(int)
        self.other: dict[str, int] = defaultdict(int)  # not relatively common
        self.per_disease: dict[str, int] = defaultdict(int)

    def refusal(self, side: str, disease_class: str, common: bool) -> str | None:
        """Why this case cannot be added, or None if it can."""
        size = self.sizes[side]
        if self.total[side] >= size:
            return f"the {side} side is full"
        if self.per_disease[disease_class] >= PER_DISEASE:
            return f"{PER_DISEASE} reports of this disease already"
        if not common and self.other[side] >= size - math.ceil(size * COMMON_SHARE):
            return f"the {side} side has its share of rarer diseases"
        return None

    def add(self, side: str, disease_class: str, common: bool) -> None:
        self.total[side] += 1
        self.other[side] += not common
        self.per_disease[disease_class] += 1

    def full(self) -> bool:
        return all(self.total[side] >= size for side, size in self.sizes.items())


# ── records ─────────────────────────────────────────────────────────


class Accepted(BaseModel):
    """One accepted report: a row of the table in git (the text itself stays local)."""

    id: str  # CaseReport_<PMID number>
    pmid: str  # PMID:n
    pmcid: str
    first_public: str  # ISO date
    side: str  # exam | dev
    disease_class: str  # Mondo class
    accepted_ids: list[str]  # the diseases of the knowledge that count as the diagnosis
    band: str  # Orphanet's prevalence band, or "" when it gives none
    kept: int  # sentences kept
    sha256: str  # of the kept text


TABLE_HEADER = (
    "id\tpmid\tpmcid\tfirst_public\tside\tdisease_class\taccepted_ids\tband\tkept\tsha256"
)
LOG_HEADER = "pmid\toutcome\treason\ta_title\tb_diagnosis\tmatched\tside"


def render_table(rows: list[Accepted]) -> str:
    lines = [TABLE_HEADER]
    for r in sorted(rows, key=lambda r: r.id):
        ids = " ".join(r.accepted_ids)
        lines.append(
            f"{r.id}\t{r.pmid}\t{r.pmcid}\t{r.first_public}\t{r.side}\t{r.disease_class}\t"
            f"{ids}\t{r.band}\t{r.kept}\t{r.sha256}"
        )
    return "\n".join(lines) + "\n"


def read_table(path: Path) -> list[Accepted]:
    return read_table_text(path.read_text(encoding="utf-8"), str(path))


def read_table_text(text: str, where: str = "the table") -> list[Accepted]:
    lines = text.splitlines()
    if not lines or lines[0] != TABLE_HEADER:
        raise ValueError(f"{where}: expected header {TABLE_HEADER!r}")
    out = []
    for line in lines[1:]:
        f = line.split("\t")
        out.append(
            Accepted(
                id=f[0],
                pmid=f[1],
                pmcid=f[2],
                first_public=f[3],
                side=f[4],
                disease_class=f[5],
                accepted_ids=f[6].split(),
                band=f[7],
                kept=int(f[8]),
                sha256=f[9],
            )
        )
    return out


class Store:
    """What the build has fetched and asked so far, kept on disk so that a build stopped
    half-way goes on without fetching or paying again: one JSON line per paper."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)

    def read(self, name: str) -> dict[str, Any]:
        path = self.folder / f"{name}.jsonl"
        if not path.exists():
            return {}
        out = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            out[record["pmid"]] = record["value"]
        return out

    def append(self, name: str, pmid: str, value: Any) -> None:
        with (self.folder / f"{name}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"pmid": pmid, "value": value}, ensure_ascii=False) + "\n")


def batches(items: list[str], size: int) -> Iterator[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


class Builder:
    """The build itself, one paper at a time in the fixed order. Everything it needs from
    outside is passed in, so the rules can be tested without a network or a model."""

    def __init__(
        self,
        *,
        mesh: Mesh,
        canonical: Callable[[str], str | None],  # an OMIM or ORPHA id -> the knowledge's disease
        find: Callable[[str], tuple[str, ...]],  # a disease name -> the diseases so named
        names_of: Callable[[str], Iterable[str]],  # a Mondo class -> its names and synonyms
        genes_of: Callable[[str], Iterable[str]],  # a disease of the knowledge -> its genes
        band_of: Callable[[str], str],  # a disease of the knowledge -> prevalence band, or ""
        ask: Callable[[str, str, list[str]], Key | None],  # annotator B
        fetch: Callable[[str], FullText | None],
        used: frozenset[str],  # PMID:n of papers already used elsewhere
        cutoff: date | None,  # first public on or after this day; None: no check (the pilot)
        selection: Selection | None = None,
    ) -> None:
        self.mesh, self.canonical, self.find = mesh, canonical, find
        self.names_of, self.genes_of, self.band_of = names_of, genes_of, band_of
        self.ask, self.fetch = ask, fetch
        self.used, self.cutoff = used, cutoff
        self.selection = selection or Selection()
        self.accepted: list[Accepted] = []
        self.texts: dict[str, str] = {}
        self.log: list[str] = []

    def _known(self, identifiers: list[str]) -> dict[str, set[str]]:
        """Mondo class -> the diseases of the knowledge it is, for the classes that are a
        rare disease of the knowledge: one Orphanet lists (OMIM also has entries for
        common conditions — osteoporosis, say — which are not what is tested)."""
        out: dict[str, set[str]] = {}
        for identifier in identifiers:
            mondo = self.mesh.mondo(identifier)
            if mondo is None:
                continue
            same = self.mesh.diseases(mondo)
            if not any(d.startswith("ORPHA:") for d in same):
                continue
            here = {c for d in same if (c := self.canonical(d))}
            if here:
                out[mondo] = here
        return out

    def a_passes(self, paper: Abstract) -> bool:
        """Annotator A names at least one disease of the knowledge: worth fetching."""
        return bool(self._known(paper.title_diseases + paper.abstract_diseases))

    def one_in_title(self, paper: Abstract) -> bool:
        """The title names exactly one rare disease of the knowledge, on a paper not used
        elsewhere: the first rules of `process`, which need nothing fetched."""
        unused = f"PMID:{paper.pmid}" not in self.used
        return unused and len(self._known(paper.title_diseases)) == 1

    def _skip(self, pmid: str, reason: str, *details: str) -> Accepted | None:
        """Log why a paper is skipped; always None, so a rule can `return self._skip(...)`."""
        cells = list(details) + [""] * (4 - len(details))
        self.log.append("\t".join([f"PMID:{pmid}", "skipped", reason, *cells]))
        return None

    def process(self, paper: Abstract, first_public: date | None) -> Accepted | None:
        """One paper through every rule; the reason it is skipped goes in the log."""
        pmid = paper.pmid
        if f"PMID:{pmid}" in self.used:
            return self._skip(pmid, "paper already used elsewhere")
        if self.cutoff is not None and (first_public is None or first_public < self.cutoff):
            return self._skip(pmid, "not first public after the cutoff")
        title = self._known(paper.title_diseases)
        a_title = " ".join(sorted(title))
        if len(title) != 1:
            reason = "A: no disease of the knowledge in the title"
            if title:
                reason = "A: more than one disease of the knowledge in the title"
            return self._skip(pmid, reason, a_title)
        ((disease_class, diseases),) = title.items()
        side = side_of(disease_class)
        common = any(self.band_of(d) == COMMON for d in diseases)
        refusal = self.selection.refusal(side, disease_class, common)
        if refusal:  # before any fetch or model call: nothing is spent on a case that cannot fit
            return self._skip(pmid, refusal, a_title, "", "", side)
        text = self.fetch(pmid)
        if text is None or not text.pmcid:
            return self._skip(pmid, "no full text from BioC", a_title)
        numbered = sentences(text.paragraphs)
        if not numbered:
            return self._skip(pmid, "no case description section", a_title)
        key = self.ask(paper.title, paper.abstract, numbered)
        if key is None:
            return self._skip(pmid, "B: unreadable reply", a_title)
        matched = set(self.find(key.diagnosis))
        details = (a_title, key.diagnosis, " ".join(sorted(matched)), side)
        if key.patients != 1:
            return self._skip(pmid, "not a single patient", *details)
        if not key.diagnostic:
            return self._skip(pmid, "diagnosis known from the start", *details)
        if not matched:
            return self._skip(pmid, "B: diagnosis not found in the knowledge", *details)
        if not matched & diseases:
            return self._skip(pmid, "A and B disagree", *details)
        diseases = diseases | matched  # entries under the very name B's diagnosis matched
        long, short = name_forms(self.names_of(disease_class))
        genes = sorted({g for d in diseases for g in self.genes_of(d)})
        kept = cut(numbered, key.reveal, long, short, genes)
        body = kept_text(numbered, kept)
        if len(body.split()) < MIN_WORDS:
            return self._skip(pmid, f"fewer than {MIN_WORDS} words before the cut", *details)
        row = Accepted(
            id=f"CaseReport_{pmid}",
            pmid=f"PMID:{pmid}",
            pmcid=text.pmcid,
            first_public=first_public.isoformat() if first_public else "",
            side=side,
            disease_class=disease_class,
            accepted_ids=sorted(diseases),
            band=next((self.band_of(d) for d in sorted(diseases) if self.band_of(d)), ""),
            kept=kept,
            sha256=checksum(body),
        )
        self.selection.add(side, disease_class, common)
        self.accepted.append(row)
        self.texts[row.id] = body
        self.log.append("\t".join([row.pmid, "accepted", "", *details]))
        return row


# ── names to look for ───────────────────────────────────────────────

_SYNONYM = re.compile(r'^synonym: "((?:[^"\\]|\\.)*)" EXACT')


def mondo_names(path: Path) -> dict[str, list[str]]:
    """Each Mondo class's name and exact synonyms (abbreviations among them), from the
    ontology file: what the cut looks for."""
    names: dict[str, list[str]] = {}
    current: list[str] | None = None
    with path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("["):
                current = None
            elif line.startswith("id: MONDO:"):
                current = names.setdefault(line[4:], [])
            elif current is not None and line.startswith("name: "):
                current.append(line[6:])
            elif current is not None and (found := _SYNONYM.match(line)):
                current.append(found.group(1).replace('\\"', '"'))
    return names


TOO_LONG = 2.2  # a written diagnosis this many times longer than the name it matched is not it


def name_index(
    names: dict[str, str], synonyms: Callable[[str], Iterable[str]]
) -> dict[str, tuple[str, ...]]:
    """Every form a disease of the knowledge is named by -> the diseases so named: each
    part of a name here (an OMIM title holds several between semicolons) and its Mondo
    class's name and exact synonyms. Two entries can share a form (OMIM's and Orphanet's
    CHARGE syndrome, which Mondo does not make one): both are kept."""
    index: dict[str, set[str]] = defaultdict(set)
    for disease in sorted(names):
        for name in (names[disease], *synonyms(disease)):
            for part in name.split(";"):
                form = part.strip().lstrip("#%+^*").strip()
                if len(form) >= 5:
                    index[form.lower()].add(disease)
    return {form: tuple(sorted(diseases)) for form, diseases in index.items()}


def find_by_name(name: str, index: dict[str, tuple[str, ...]], threshold: int) -> tuple[str, ...]:
    """The diseases named most like what is written, when close enough: find_disease's
    matching (WRatio, ties in order), over every form of each name. WRatio forgives a
    partial match, so a long phrase that merely contains a disease's name would match it:
    what is written may not be more than TOO_LONG times as long as the form it matches."""
    from rapidfuzz import fuzz, process, utils

    written = name.strip()
    if len(written) < 3:
        return ()
    hits = process.extract(
        written, list(index), scorer=fuzz.WRatio, processor=utils.default_process, limit=20
    )
    hits.sort(key=lambda h: (-h[1], h[0]))
    for form, score, _ in hits:
        if round(score) < threshold:
            return ()
        if len(written) <= TOO_LONG * len(form):
            return index[form]
    return ()

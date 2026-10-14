"""From a clinical note to HPO terms: what the agent takes, from what a clinician writes.

Three readers, one method — read(text) gives the note's findings, each with the
words it rests on, whether the patient has it, and its HPO term:

    NoteReader        ours. The model reads the note and lists each finding: the words
                      it rests on, the finding in clinical terms, and whether the patient
                      has it (present), the note denies it (absent), or it is a
                      relative's (family). A search over HPO's names and synonyms —
                      hybrid, the same as for the disease texts — finds candidate terms
                      for each; a finding named exactly as HPO names a term is coded
                      with it, and the model picks among the candidates for the rest, or
                      none. The model never writes an id itself, and a finding whose
                      words are not in the note is not coded.
    DirectReader      the model asked for the HPO ids outright: what grounding the ids
                      in the ontology is measured against.
    DictionaryReader  no model: every HPO name or exact synonym that appears in the text,
                      the longest first. The classic approach: free, fast, literal.

Each read is one trace in MLflow: the model calls inside it, and the search for
each finding's candidates as a retriever span.
"""

import functools
import re
from typing import Any, Literal

import mlflow
from mlflow.entities import SpanType
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

from raredx.knowledge.hpo import HPO
from raredx.knowledge.text_index import TextIndex
from raredx.llm import Budget, Tally, ask_json

Status = Literal["present", "absent", "family"]
CodedBy = Literal["name", "model", "dictionary"]

PROMPT_VERSION = "note-v3"
DIRECT_PROMPT_VERSION = "note-direct-v1"
BY_FINDING, BY_WORDS = 8, 4  # candidate terms searched for with each, before merging


class Finding(BaseModel):
    """One finding the note states, and how it was coded."""

    quote: str = Field(description="The words of the note it rests on")
    start: int | None = Field(default=None, description="Where those words are; None if absent")
    end: int | None = None
    finding: str = Field(description="The finding in clinical terms, as the reader put it")
    status: Status = "present"
    hpo_id: str | None = None
    label: str | None = None
    coded_by: CodedBy | None = None
    uncoded: str | None = Field(default=None, description="Why no term is given")


def terms(findings: list[Finding], status: Status = "present") -> list[str]:
    """The distinct terms of the findings with this status, in the note's order."""
    return list(dict.fromkeys(f.hpo_id for f in findings if f.hpo_id and f.status == status))


class Label(BaseModel):
    """A name or synonym of an HPO term, as the term index holds it."""

    text: str
    hpo_id: str
    name: str  # the term's name


def labels(hpo: HPO) -> list[Label]:
    """What the term index is built from: each finding term's name, and its synonyms that
    say the same or nearly the same (EXACT, RELATED) — not the broader or narrower ones."""
    out = []
    for hpo_id, name in hpo.findings:
        out.append(Label(text=name, hpo_id=hpo_id, name=name))
        seen = {name.lower()}
        for text, scope, _ in hpo.synonyms(hpo_id):
            if scope in ("EXACT", "RELATED") and text.lower() not in seen:
                seen.add(text.lower())
                out.append(Label(text=text, hpo_id=hpo_id, name=name))
    return out


def locate(quote: str, text: str) -> tuple[int, int] | None:
    """Where the quoted words are in the text: as written, else ignoring case, else
    ignoring the spacing and punctuation between the words. None if they are not there."""
    if not quote.strip():
        return None
    for haystack, needle in ((text, quote), (text.lower(), quote.lower())):
        i = haystack.find(needle)
        if i >= 0:
            return i, i + len(needle)
    words = re.findall(r"\w+", quote)
    if not words:
        return None
    m = re.search(r"\W+".join(map(re.escape, words)), text, re.IGNORECASE)
    return (m.start(), m.end()) if m else None


def _normal(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.lower()))


@functools.cache
def _exact_names(hpo: HPO, abbreviations: bool = True) -> dict[str, frozenset[str]]:
    """Every finding term's name and EXACT synonyms, normalised, with the terms they name;
    without the abbreviations, if asked: in running text "S4" is more often a spinal
    level than a fourth heart sound."""
    names: dict[str, set[str]] = {}
    for hpo_id, name in hpo.findings:
        synonyms = [
            text
            for text, scope, kind in hpo.synonyms(hpo_id)
            if scope == "EXACT" and (abbreviations or kind != "abbreviation")
        ]
        for text in [name, *synonyms]:
            names.setdefault(_normal(text), set()).add(hpo_id)
    return {k: frozenset(v) for k, v in names.items() if k}


LONGEST_NAME = 12  # words in the longest name looked for in a text


def name_matches(text: str, hpo: HPO) -> list[tuple[int, int, frozenset[str]]]:
    """Every HPO name or exact synonym (not abbreviations) written in the text, as
    (start, end, terms): scanning word by word, the longest name first."""
    names = _exact_names(hpo, abbreviations=False)
    words = list(re.finditer(r"\w+", text))
    lowered = [w[0].lower() for w in words]
    found, i = [], 0
    while i < len(words):
        for n in range(min(LONGEST_NAME, len(words) - i), 0, -1):
            ids = names.get(" ".join(lowered[i : i + n]))
            if ids:
                found.append((words[i].start(), words[i + n - 1].end(), ids))
                i += n
                break
        else:
            i += 1
    return found


def sentence_of(text: str, start: int, end: int, most: int = 300) -> str:
    """The sentence around a span, at most `most` characters of it."""
    left = max(text.rfind(c, 0, start) for c in ".;\n") + 1
    rights = [i for i in (text.find(c, end) for c in ".;\n") if i >= 0]
    right = min(rights) + 1 if rights else len(text)
    left, right = max(left, start - most // 2), min(right, end + most // 2)
    return " ".join(text[left:right].split())


# ── ours: the model reads, the ontology codes ───────────────────────


EXTRACT_PROMPT = """\
You read clinical text and list the phenotypic findings it describes, so that they can \
be coded in the Human Phenotype Ontology (HPO).

A finding is an abnormality of the body or of how it works: a sign, a symptom, an \
examination finding, an abnormal imaging, laboratory or test result (a vitamin \
deficiency, a raised enzyme), a developmental, cognitive or behavioural problem, a \
problem of growth. General findings count as well as specific ones ("renal anomalies", \
"skin lesions", "cancer"). A disease that is itself a clinical finding counts (asthma, \
epilepsy, cataract, cardiomyopathy, albinism), and so does a finding named within the \
name of a syndrome ("nevoid basal cell carcinoma syndrome": nevi, basal cell carcinoma); \
the syndrome itself does not. Normal findings, procedures, treatments, genes and \
variants do not.

For each finding give:
- "quote": the words of the text that state it, copied exactly: the shortest span that \
names it, such as "floppy", "poor sucking", "IQ was estimated to be 20-30".
- "finding": the finding in standard clinical terms, as HPO would name it, keeping \
laterality, severity and location when the text gives them: "Hypotonia", "Poor suck", \
"Severe intellectual disability", "Bilateral cataract".
- "status": "present" when the patient has it; "absent" when the text says the patient \
does not; "family" when it is about a relative, not the patient. In a text about a \
disease rather than one patient, a feature of the disease is "present".

List each finding once. Findings named together are listed apart: "hypoplastic or \
absent thumbs" and "cleft lip and palate" are two each, "ophthalmic, auditory and renal \
anomalies" three; a range is its two ends ("mild to moderate intellectual disability": \
mild intellectual disability, moderate intellectual disability).

Reply with only a JSON object:
{"findings": [{"quote": "...", "finding": "...", "status": "present"}]}"""

LINK_PROMPT = """\
You code findings in the Human Phenotype Ontology (HPO).

Part 1. For each numbered finding you are given the words of the clinical text, the \
finding in clinical terms, and HPO terms that a search found for it. Choose the term that \
says the same as the finding. If none does, choose the most specific term that is still \
true of the finding, even if it is more general. Choose only from the terms given for \
that finding; choose null if none of them is true of it.

Part 2. Each lettered item is an HPO term whose name is written in the text, with the \
sentence it is written in. Say what the text states of it: "present" (the patient has \
it; in a text about a disease, the disease shows it), "absent" (the text says the \
patient does not have it), "family" (a relative has it), or "none" (the words do not \
mean this finding there: "collecting system" is not hoarding).

Reply with only a JSON object, one entry per finding and per item:
{"codes": [{"n": 1, "hpo_id": "HP:0001252"}, {"n": 2, "hpo_id": null}],
 "checked": [{"item": "A", "status": "present"}]}"""


class _Mention(BaseModel):
    quote: str
    finding: str
    status: Status


class _Mentions(BaseModel):
    findings: list[_Mention]


class _Code(BaseModel):
    n: int
    hpo_id: str | None


class _Check(BaseModel):
    item: str
    status: Status | Literal["none"]


class _Codes(BaseModel):
    codes: list[_Code] = []
    checked: list[_Check] = []


class _Named(BaseModel):
    """A term the dictionary found written in the note, outside every finding the model
    listed: the model is asked what the note says of it."""

    hpo_id: str
    quote: str
    start: int
    end: int
    sentences: str


def _letters(i: int) -> str:
    """A, B, ..., Z, AA, AB, ...: the items' names in the prompt."""
    return _letters(i // 26 - 1) + chr(65 + i % 26) if i >= 26 else chr(65 + i)


class NoteReader:
    name = "note-reader"

    def __init__(
        self,
        api: OpenAI,
        model: str,
        hpo: HPO,
        index: TextIndex[Label],
        *,
        budget: Budget | None = None,
    ) -> None:
        self.api, self.model, self.hpo, self.index, self.budget = api, model, hpo, index, budget

    def config(self) -> dict[str, Any]:
        return {
            "reader": self.name,
            "model": self.model,
            "prompt_version": PROMPT_VERSION,
            "hpo_release": self.hpo.release,
            "term_index": f"{len(self.index.passages)} names and synonyms; "
            f"{BY_FINDING}+{BY_WORDS} candidates per finding",
            "dictionary": "names and exact synonyms, no abbreviations; checked by the model",
        }

    def _ask[M: BaseModel](self, system: str, user: str, reply: type[M], tally: Tally | None) -> M:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return ask_json(
            self.api,
            self.model,
            messages,
            lambda content: reply.model_validate_json(content or ""),
            budget=self.budget,
            tally=tally,
        )

    @mlflow.trace(name="candidate terms", span_type=SpanType.RETRIEVER)
    def candidates(self, finding: str, quote: str) -> list[tuple[str, str]]:
        """HPO terms for one finding, as (id, name): those the search finds for the
        finding in clinical terms, then for the note's own words."""
        found: dict[str, str] = {}
        for query, wanted in ((finding, BY_FINDING), (quote, BY_WORDS)):
            added = 0
            for label, _ in self.index.search(query, wanted * 3):
                if label.hpo_id not in found:
                    found[label.hpo_id] = label.name
                    added += 1
                if added == wanted:
                    break
        return list(found.items())

    @mlflow.trace(name="read note", span_type=SpanType.CHAIN)
    def read(self, text: str, tally: Tally | None = None) -> list[Finding]:
        """The note's findings, coded. `tally` sums the model calls it made.

        1. The model lists the findings (EXTRACT_PROMPT).
        2. A finding named exactly as HPO names a term is coded with it; for the others
           the term index offers candidates.
        3. The dictionary looks for HPO's names in the note. A name inside a finding's
           words takes that finding's status; one outside them all is shown to the model.
        4. One more call (LINK_PROMPT): the model codes each finding from its candidates,
           and says what the note states of each name found outside.
        """
        mentions = self._ask(EXTRACT_PROMPT, text, _Mentions, tally).findings
        exact = _exact_names(self.hpo)
        findings: list[Finding] = []
        ask: dict[int, list[tuple[str, str]]] = {}  # finding number -> its candidates
        for mention in mentions:
            where = locate(mention.quote, text)
            finding = Finding(
                quote=mention.quote,
                start=where[0] if where else None,
                end=where[1] if where else None,
                finding=mention.finding,
                status=mention.status,
            )
            # Named exactly as HPO names a term — in clinical terms, else in the note's own
            # words — it is that term. Otherwise the model chooses among candidates.
            named = exact.get(_normal(mention.finding), frozenset())
            if len(named) != 1:
                named = exact.get(_normal(mention.quote), frozenset())
            if where is None:
                finding.uncoded = "its words are not in the note"
            elif len(named) == 1:
                finding.hpo_id = next(iter(named))
                finding.label = self.hpo.term(finding.hpo_id)[1]
                finding.coded_by = "name"
            else:
                ask[len(findings) + 1] = self.candidates(mention.finding, mention.quote)
            findings.append(finding)
        inside, outside = self._names(text, findings)
        if ask or outside:
            self._link(findings, ask, outside, tally)
        return findings + self._named_inside(inside, findings, text)

    def _names(
        self, text: str, findings: list[Finding]
    ) -> tuple[list[tuple[int, int, str, Finding]], list[_Named]]:
        """The dictionary's names in the note: those inside a finding's words, with the
        finding; and those outside them all, one per term, to be checked."""
        spans = [(f.start, f.end, f) for f in findings if f.start is not None and f.end is not None]
        coded = {f.hpo_id for f in findings if f.hpo_id}
        inside: list[tuple[int, int, str, Finding]] = []
        outside: dict[str, _Named] = {}
        for start, end, ids in name_matches(text, self.hpo):
            container = next((f for a, b, f in spans if a <= start and end <= b), None)
            for hpo_id in sorted(ids):
                if container is not None:
                    inside.append((start, end, hpo_id, container))
                elif hpo_id in coded:
                    continue
                elif hpo_id not in outside:
                    outside[hpo_id] = _Named(
                        hpo_id=hpo_id, quote=text[start:end], start=start, end=end,
                        sentences=sentence_of(text, start, end),
                    )  # fmt: skip
                elif outside[hpo_id].sentences.count(" … ") < 1:  # at most two sentences
                    outside[hpo_id].sentences += " … " + sentence_of(text, start, end)
        return inside, list(outside.values())

    def _named_inside(
        self, inside: list[tuple[int, int, str, Finding]], findings: list[Finding], text: str
    ) -> list[Finding]:
        """Names found inside a finding's words that say more than its code: "basal cell
        carcinoma" in "nevoid basal cell carcinoma syndrome", coded as nevi. A name that
        is the finding's own term, or a more general one, adds nothing."""
        coded = {f.hpo_id for f in findings if f.hpo_id}
        added: list[Finding] = []
        for start, end, hpo_id, container in inside:
            if hpo_id in coded:
                continue
            if container.hpo_id and self.hpo.relation(container.hpo_id, hpo_id) == "more specific":
                continue
            label = self.hpo.term(hpo_id)[1]
            added.append(Finding(quote=text[start:end], start=start, end=end, finding=label,
                                 status=container.status, hpo_id=hpo_id, label=label,
                                 coded_by="dictionary"))  # fmt: skip
            coded.add(hpo_id)
        return added

    def _link(
        self,
        findings: list[Finding],
        ask: dict[int, list[tuple[str, str]]],
        outside: list[_Named],
        tally: Tally | None,
    ) -> None:
        """The model picks each finding's term among its candidates, and says what the
        note states of each name found outside the findings (added to `findings`)."""
        blocks = []
        for n, offered in ask.items():
            f = findings[n - 1]
            lines = "\n".join(f"   - {i} {name}" for i, name in offered)
            blocks.append(f'{n}. Text: "{f.quote}" | Finding: {f.finding}\n{lines}')
        items = {_letters(i): named for i, named in enumerate(outside)}
        for letter, named in items.items():
            label = self.hpo.term(named.hpo_id)[1]
            blocks.append(f"{letter}. {named.hpo_id} {label}\n   Written in: {named.sentences}")
        reply = self._ask(LINK_PROMPT, "\n\n".join(blocks), _Codes, tally)
        chosen = {c.n: c.hpo_id for c in reply.codes}
        for n, offered in ask.items():
            f, hpo_id = findings[n - 1], chosen.get(n)
            names = dict(offered)
            if hpo_id is None:
                f.uncoded = "no term found fits it"
            elif hpo_id not in names:
                f.uncoded = f"the model chose {hpo_id}, which was not offered"
            else:
                f.hpo_id, f.label, f.coded_by = hpo_id, names[hpo_id], "model"
        checked = {c.item: c.status for c in reply.checked}
        coded = {f.hpo_id for f in findings if f.hpo_id}
        for letter, named in items.items():
            status = checked.get(letter, "none")
            if status == "none" or named.hpo_id in coded:
                continue
            label = self.hpo.term(named.hpo_id)[1]
            findings.append(Finding(quote=named.quote, start=named.start, end=named.end,
                                    finding=label, status=status, hpo_id=named.hpo_id,
                                    label=label, coded_by="dictionary"))  # fmt: skip


# ── the model alone ─────────────────────────────────────────────────


DIRECT_PROMPT = """\
You read clinical text and code the phenotypic findings it describes in the Human \
Phenotype Ontology (HPO).

A finding is an abnormality of the body or of how it works: a sign, a symptom, an \
examination finding, an abnormal imaging, laboratory or test result, a developmental, \
cognitive or behavioural problem, a problem of growth. The name of a syndrome or genetic \
disease is not a finding, nor are normal findings, procedures, treatments, genes and \
variants.

For each finding give the words of the text that state it ("quote", copied exactly), \
its HPO term ("hpo_id", such as "HP:0001252", and "label", the term's name), and \
"status": "present", "absent" (the text says the patient does not have it) or "family" \
(it is about a relative).

Reply with only a JSON object:
{"findings": [{"quote": "...", "hpo_id": "HP:...", "label": "...", "status": "present"}]}"""

_HPO_ID = re.compile(r"HP:\d{7}")


class _Direct(BaseModel):
    quote: str
    hpo_id: str
    label: str = ""
    status: Status


class _DirectReply(BaseModel):
    findings: list[_Direct]


class DirectReader:
    name = "model-direct"

    def __init__(self, api: OpenAI, model: str, hpo: HPO, *, budget: Budget | None = None) -> None:
        self.api, self.model, self.hpo, self.budget = api, model, hpo, budget

    def config(self) -> dict[str, Any]:
        return {
            "reader": self.name,
            "model": self.model,
            "prompt_version": DIRECT_PROMPT_VERSION,
            "hpo_release": self.hpo.release,
        }

    @mlflow.trace(name="read note", span_type=SpanType.CHAIN)
    def read(self, text: str, tally: Tally | None = None) -> list[Finding]:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": DIRECT_PROMPT},
            {"role": "user", "content": text},
        ]
        reply = ask_json(
            self.api,
            self.model,
            messages,
            lambda c: _DirectReply.model_validate_json(c or ""),
            budget=self.budget,
            tally=tally,
        )
        findings = []
        for d in reply.findings:
            where = locate(d.quote, text)
            finding = Finding(
                quote=d.quote,
                start=where[0] if where else None,
                end=where[1] if where else None,
                finding=d.label,
                status=d.status,
            )
            if not _HPO_ID.fullmatch(d.hpo_id.strip()):
                finding.uncoded = f"not an HPO id: {d.hpo_id!r}"
            else:
                # As given: an id the release does not know is the model's error, scored so.
                finding.hpo_id, finding.coded_by = d.hpo_id.strip(), "model"
                current = self.hpo.current(finding.hpo_id)
                finding.label = self.hpo.term(current)[1] if current else None
            findings.append(finding)
        return findings


# ── no model ────────────────────────────────────────────────────────


class DictionaryReader:
    name = "dictionary"

    def __init__(self, hpo: HPO) -> None:
        self.hpo = hpo

    def config(self) -> dict[str, Any]:
        return {
            "reader": self.name,
            "hpo_release": self.hpo.release,
            "dictionary": "names and exact synonyms, no abbreviations",
        }

    @mlflow.trace(name="dictionary", span_type=SpanType.PARSER)
    def read(self, text: str, tally: Tally | None = None) -> list[Finding]:
        findings = []
        for start, end, ids in name_matches(text, self.hpo):
            for hpo_id in sorted(ids):
                label = self.hpo.term(hpo_id)[1]
                findings.append(Finding(quote=text[start:end], start=start, end=end,
                                        finding=label, hpo_id=hpo_id, label=label,
                                        coded_by="dictionary"))  # fmt: skip
        return findings


Reader = NoteReader | DirectReader | DictionaryReader

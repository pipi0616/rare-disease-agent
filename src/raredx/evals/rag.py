"""Measuring the RAG tool's retrieval, without a model (chapter 33).

Two uses of the texts, two kinds of question, all from the development cases and each
asked under its case's mask (the case's paper hidden, and every disease known only
from it):

- find: the patient's findings as the query. Is the confirmed disease among the ten
  diseases the best passages are about? The tool used to nominate candidates, as in
  chapter 18.
- inheritance / feature: a question about the confirmed disease — how is it inherited;
  does it have one of its annotated features? Is a passage about that disease, saying
  the answer, among the five returned? The tool used to check a candidate.

The answer keys are not the indexed texts: inheritance comes from Orphanet's natural
history file, features from HPO's annotation. A passage "says" the answer when it names
it — the inheritance's usual wording, the feature's label or an exact synonym. The
test is strict and mechanical: a paraphrase is missed, so the numbers are a floor.
"""

import re
import statistics
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from raredx.data.cases import Case
from raredx.evals import scoring
from raredx.knowledge.hpo import HPO
from raredx.knowledge.text_index import Mode, TextIndex
from raredx.knowledge.texts import Passage

Kind = Literal["find", "inheritance", "feature"]
KINDS: tuple[Kind, ...] = ("find", "inheritance", "feature")
FIND_DEPTH, FIND_K, RRF_K = 50, 10, 60  # as chapter 18's no-model ranking
RETURNED, DEEP = 5, 30  # passages returned for a question; candidates a reranker sees
FEATURES = 2  # feature questions per disease

# Orphanet's types of inheritance, as a text would say them. Unknown, not applicable
# and the like have no wording to look for: no question is asked of them.
INHERITANCE = {
    "Autosomal recessive": r"autosomal[- ]recessive",
    "Autosomal dominant": r"autosomal[- ]dominant",
    "X-linked recessive": r"x[- ]linked",
    "X-linked dominant": r"x[- ]linked",
    "Mitochondrial inheritance": r"mitochondrial (inheritance|dna|genome)|maternal(ly)? inherit",
    "Multigenic/multifactorial": r"multifactorial|polygenic|multigenic",
    "Semi-dominant": r"semi-?dominant",
    "Y-linked": r"y[- ]linked",
    "Oligogenic": r"oligogenic",
}


class Question(BaseModel):
    kind: Kind
    source: str
    case_id: str
    text: str
    disease: str  # the confirmed disease, as the knowledge names it
    accepted: list[str]  # every id that counts as it (find)
    answer: list[str]  # patterns a passage must match to say the answer (facts)
    hide_pmids: list[str]
    hide_diseases: list[str]


class Config(BaseModel):
    mode: Mode = "hybrid"
    filtered: bool = False  # fact questions: search only the disease's passages
    rerank: str = ""  # a cross-encoder's name, or none

    def label(self) -> str:
        return " ".join(
            [
                self.mode,
                *(["filtered"] if self.filtered else []),
                *([self.rerank] if self.rerank else []),
            ]
        )


def inheritance_key(path: Path) -> dict[str, list[str]]:
    """ORPHA id -> Orphanet's types of inheritance for it, those a text can be checked for."""
    out = {}
    for disorder in ET.parse(path).getroot().iter("Disorder"):
        types = [
            name
            for t in disorder.iter("TypeOfInheritance")
            if (name := t.findtext("Name") or "") in INHERITANCE
        ]
        if types:
            out[f"ORPHA:{disorder.findtext('OrphaCode')}"] = types
    return out


def _words(text: str) -> str:
    return r"\b" + re.escape(text.lower())


def questions(
    cases: dict[str, list[Case]],
    hpo: HPO,
    same: scoring.Same,
    inheritance: dict[str, list[str]],
) -> list[Question]:
    """Every question the development cases give: one find per case; per case whose
    disease Orphanet gives an inheritance for, one on it; FEATURES on its features."""
    by_disease: dict[str, list[str]] = defaultdict(list)  # inheritance by knowledge disease
    for orpha, types in inheritance.items():
        if disease := hpo.canonical(orpha):
            by_disease[disease] += [t for t in types if t not in by_disease[disease]]
    out = []
    for source, chosen in cases.items():
        for case in chosen:
            pmids = [case.pmid] if case.pmid else []
            hidden = sorted(hpo.known_only_from(frozenset(pmids))) if pmids else []
            accepted = sorted(
                {
                    c
                    for d in scoring.accepted_ids(case.disease_id, case.also_accepted, same)
                    if (c := hpo.canonical(d))
                }
            )
            if not accepted:
                continue
            disease = (
                accepted[0]
                if hpo.canonical(case.disease_id) is None
                else str(hpo.canonical(case.disease_id))
            )
            name = hpo.names.get(disease, case.disease_label)
            base: dict[str, Any] = {
                "source": source,
                "case_id": case.id,
                "disease": disease,
                "accepted": accepted,
                "hide_pmids": pmids,
                "hide_diseases": hidden,
            }
            out.append(Question(kind="find", text="; ".join(case.hpo_labels), answer=[], **base))
            if disease in hidden:
                continue  # nothing about it may be read under this mask
            if inherited := by_disease.get(disease):
                out.append(
                    Question(
                        kind="inheritance",
                        text=f"{name}: mode of inheritance",
                        answer=sorted({INHERITANCE[t] for t in inherited}),
                        **base,
                    )
                )
            for feature in _features(hpo, disease, frozenset(pmids)):
                synonyms = [s for s, scope, _ in hpo.synonyms(feature.term) if scope == "EXACT"]
                out.append(
                    Question(
                        kind="feature",
                        text=f"{name}: {feature.label}",
                        answer=[_words(t) for t in (feature.label, *synonyms)],
                        **base,
                    )
                )
    return out


def _features(hpo: HPO, disease: str, masked: frozenset[str]) -> list[Any]:
    """The disease's most frequent features with a plain name: the ones a description
    of it most likely mentions."""
    seen = [
        f
        for f in hpo.features(disease, masked)
        if not f.absent and len(f.label.split()) <= 4 and not f.label.startswith("Abnormal")
    ]
    seen.sort(key=lambda f: (-(f.frequency.fraction or 0), -f.information, f.term))
    return seen[:FEATURES]


Rerank = Callable[[str, list[str]], list[float]]


def ask(
    index: TextIndex[Passage], q: Question, config: Config, rerank: Rerank | None
) -> list[Passage]:
    """What the tool returns for a question, best first: the find question's 50
    passages, a fact question's 5 (distinct returned texts)."""
    only = [q.disease] if config.filtered and q.kind != "find" else []
    depth = FIND_DEPTH if q.kind == "find" else (DEEP if rerank else RETURNED * 4)
    found = [
        p
        for p, _ in index.search(
            q.text,
            depth,
            config.mode,
            only=only,
            hide_diseases=q.hide_diseases,
            hide_pmids=q.hide_pmids,
        )
    ]
    if rerank and q.kind != "find":
        scores = rerank(q.text, [p.text for p in found])
        found = [p for _, p in sorted(zip(scores, found, strict=True), key=lambda x: -x[0])]
    if q.kind == "find":
        return found
    out, seen = [], set()
    for p in found:  # a parent returned once, however many of its small pieces matched
        key = p.parent or p.text
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out[:RETURNED]


def score(q: Question, passages: Sequence[Passage]) -> dict[str, float]:
    """One question's measures: find — the disease among the ten credited (and a
    passage about it among the first ten); facts — a passage about the disease, one
    saying the answer, among those returned, and the reciprocal rank of the first."""
    accepted = set(q.accepted)
    if q.kind == "find":
        credit: dict[str, float] = defaultdict(float)
        for rank, p in enumerate(passages):
            for d in p.disease_ids:
                credit[d] += 1 / (RRF_K + rank) / len(p.disease_ids)
        top = sorted(credit, key=lambda d: (-credit[d], d))[:FIND_K]
        return {
            "disease@10": float(bool(accepted & set(top))),
            "passage@10": float(any(accepted & set(p.disease_ids) for p in passages[:10])),
        }
    about = [q.disease in p.disease_ids for p in passages]
    says = [
        a and any(re.search(pattern, (p.parent or p.text).lower()) for pattern in q.answer)
        for a, p in zip(about, passages, strict=True)
    ]
    first = next((i for i, s in enumerate(says, 1) if s), None)
    return {
        "about@5": float(any(about)),
        "answer@5": float(any(says)),
        "rr": 1 / first if first else 0.0,
    }


def summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Mean of each measure, per kind of question (all sources) and per kind and source."""
    groups: dict[str, list[dict[str, float]]] = defaultdict(list)
    for row in rows:
        groups[row["kind"]].append(row["scores"])
        groups[f"{row['kind']}/{row['source']}"].append(row["scores"])
    return {
        g: {m: statistics.fmean(s[m] for s in scores) for m in scores[0]} | {"n": len(scores)}
        for g, scores in groups.items()
    }


def paired(
    a: list[dict[str, Any]], b: list[dict[str, Any]], kind: Kind, measure: str
) -> tuple[int, int, float]:
    """Two runs on the same questions, question by question: on how many the first
    does better (a hit the second misses; for rr, the answer ranked higher), on how
    many the second, and the sign test's p."""
    score_b = {(r["source"], r["question"]): r["scores"][measure] for r in b if r["kind"] == kind}
    only_a = only_b = 0
    for r in a:
        if r["kind"] != kind or (key := (r["source"], r["question"])) not in score_b:
            continue
        x, y = r["scores"][measure], score_b[key]
        only_a += x > y
        only_b += y > x
    return only_a, only_b, scoring.sign_test(only_a, only_b)

"""Systems under evaluation, and the boundary they work behind.

A system sees a Question — the phenotype — and nothing else: no diagnosis, no
gene, no source paper. Whatever the system is, a fixed baseline or the agent,
it answers with a ranked list of Candidates, best first.

Two reference systems live here to calibrate the scorer, not to be reported:
Oracle must score 100% or the scorer is wrong; Popularity is the floor any
real system has to clear.
"""

from collections import Counter, defaultdict
from typing import Protocol

from pydantic import BaseModel

from raredx.data.cases import Case


class Question(BaseModel):
    """Everything a system is allowed to see about a case."""

    case_id: str
    hpo_ids: list[str]
    hpo_labels: list[str]
    sex: str | None


class Candidate(BaseModel):
    disease_name: str
    disease_id: str | None = None  # OMIM number; how the scorer recognises the disease
    gene: str | None = None


class System(Protocol):
    name: str

    def predict(self, question: Question) -> list[Candidate]: ...


def question_of(case: Case) -> Question:
    return Question(case_id=case.id, hpo_ids=case.hpo_ids, hpo_labels=case.hpo_labels, sex=case.sex)


def answer_of(case: Case) -> Candidate:
    return Candidate(disease_name=case.disease_label, disease_id=case.disease_id, gene=case.gene)


class Oracle:
    """Answers every case with its confirmed diagnosis. Cheats by design."""

    name = "oracle"

    def __init__(self, answers: dict[str, Candidate]) -> None:
        self.answers = answers

    @classmethod
    def from_cases(cls, cases: list[Case]) -> "Oracle":
        return cls({c.id: answer_of(c) for c in cases})

    def predict(self, question: Question) -> list[Candidate]:
        return [self.answers[question.case_id]]


class Popularity:
    """The same diseases for every patient: the ones reported in the most papers.

    Counted by paper, not by case, so one 462-patient report does not decide
    the list. Built from cases outside the set being scored, so a dev set never
    grades its own prior.
    """

    name = "popularity"

    def __init__(self, ranked: list[Candidate]) -> None:
        self.ranked = ranked

    @classmethod
    def from_cases(cls, pool: list[Case], k: int = 10) -> "Popularity":
        papers: dict[str, set[str]] = defaultdict(set)
        genes: dict[str, Counter[str]] = defaultdict(Counter)
        labels: dict[str, str] = {}
        for c in pool:
            papers[c.disease_id].add(c.pmid)
            labels[c.disease_id] = c.disease_label
            if c.gene:
                genes[c.disease_id][c.gene] += 1
        top = sorted(papers, key=lambda d: (-len(papers[d]), d))[:k]
        return cls(
            [
                Candidate(
                    disease_name=labels[d],
                    disease_id=d,
                    gene=genes[d].most_common(1)[0][0] if genes[d] else None,
                )
                for d in top
            ]
        )

    def predict(self, question: Question) -> list[Candidate]:
        return list(self.ranked)

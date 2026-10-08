"""Scoring: is the confirmed diagnosis in the answer, and how high?

The rules are fixed before any model is run:

- A disease is found when a candidate's OMIM number equals the case's. Names
  are not compared: one disease has many spellings.
- A gene is found when a candidate names the causal gene, ignoring case. Cases
  without a causal gene are left out of the gene numbers.
- The rank is the candidate's position in the answer, best first.
- A case with no answer — the system failed or returned nothing — is a miss.
  It stays in the denominator; dropping failures would inflate every number.

Every rate comes with a 95% Wilson interval, so a reader can see how much of a
difference between two runs is noise.
"""

import math
import re

from pydantic import BaseModel

from raredx.data.cases import Case
from raredx.evals.systems import Candidate

KS = (1, 3, 5, 10)


def normalize_omim(value: str | None) -> str | None:
    """'OMIM:621101', 'MIM 621101', '621101' -> 'OMIM:621101'; anything else -> None."""
    match = re.search(r"(?<!\d)(\d{6})(?!\d)", value or "")
    return f"OMIM:{match.group(1)}" if match else None


class CaseScore(BaseModel):
    case_id: str
    answered: bool
    disease_rank: int | None  # 1 = first candidate; None = not found
    has_gene: bool
    gene_rank: int | None


def score_case(case: Case, candidates: list[Candidate]) -> CaseScore:
    disease_rank = next(
        (i for i, c in enumerate(candidates, 1) if normalize_omim(c.disease_id) == case.disease_id),
        None,
    )
    gene_rank = None
    if case.gene:
        truth = case.gene.casefold()
        gene_rank = next(
            (
                i
                for i, c in enumerate(candidates, 1)
                if c.gene and c.gene.strip().casefold() == truth
            ),
            None,
        )
    return CaseScore(
        case_id=case.id,
        answered=bool(candidates),
        disease_rank=disease_rank,
        has_gene=case.gene is not None,
        gene_rank=gene_rank,
    )


def wilson(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


class Rate(BaseModel):
    hits: int
    n: int
    rate: float
    low: float
    high: float


def rate(hits: int, n: int) -> Rate:
    low, high = wilson(hits, n)
    return Rate(hits=hits, n=n, rate=hits / n if n else 0.0, low=low, high=high)


class Summary(BaseModel):
    n_cases: int
    n_answered: int
    disease: dict[int, Rate]  # top-k -> rate
    gene: dict[int, Rate]


def summarize(scores: list[CaseScore]) -> Summary:
    with_gene = [s for s in scores if s.has_gene]

    def found(rank: int | None, k: int) -> bool:
        return rank is not None and rank <= k

    return Summary(
        n_cases=len(scores),
        n_answered=sum(s.answered for s in scores),
        disease={k: rate(sum(found(s.disease_rank, k) for s in scores), len(scores)) for k in KS},
        gene={k: rate(sum(found(s.gene_rank, k) for s in with_gene), len(with_gene)) for k in KS},
    )


def render(summary: Summary, title: str) -> str:
    def cell(r: Rate) -> str:
        return f"{r.rate * 100:5.1f}% [{r.low * 100:4.1f}–{r.high * 100:4.1f}]"

    n_gene = summary.gene[KS[0]].n
    lines = [
        f"{title} · {summary.n_cases} cases, {summary.n_answered} answered",
        "".ljust(9) + "".join(f"top-{k}".ljust(22) for k in KS),
        "disease".ljust(9) + "".join(cell(summary.disease[k]).ljust(22) for k in KS),
        "gene".ljust(9) + "".join(cell(summary.gene[k]).ljust(22) for k in KS) + f"(n={n_gene})",
    ]
    return "\n".join(lines)

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


def ranks(
    candidates: list[Candidate], disease_id: str, gene: str | None
) -> tuple[int | None, int | None]:
    """Where the confirmed disease and gene first appear in an answer (1 = top); None = absent."""
    disease_rank = next(
        (i for i, c in enumerate(candidates, 1) if normalize_omim(c.disease_id) == disease_id),
        None,
    )
    gene_rank = None
    if gene:
        truth = gene.casefold()
        gene_rank = next(
            (
                i
                for i, c in enumerate(candidates, 1)
                if c.gene and c.gene.strip().casefold() == truth
            ),
            None,
        )
    return disease_rank, gene_rank


def found(rank: int | None, k: int) -> bool:
    return rank is not None and rank <= k


def score_case(case: Case, candidates: list[Candidate]) -> CaseScore:
    disease_rank, gene_rank = ranks(candidates, case.disease_id, case.gene)
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


def sign_test(wins: int, losses: int) -> float:
    """Two-sided exact sign test for a paired comparison on the same cases.

    Only the cases where the two systems disagree count: if neither were better,
    each would win half of them. The p-value is the chance of a split at least
    this lopsided under that coin toss.
    """
    n = wins + losses
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(wins, losses) + 1)) / 2.0**n
    return min(1.0, 2 * tail)


def p_value(p: float) -> str:
    """A p-value as it is reported: three decimals, and "p < 0.001" below that rather
    than a misleading "p = 0.000"."""
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


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


def summary_from_counts(
    disease_hits: dict[int, int],
    n_cases: int,
    gene_hits: dict[int, int],
    n_gene: int,
    n_answered: int,
) -> Summary:
    """A Summary from hit counts at each k. n_gene counts only cases that have a causal gene."""
    return Summary(
        n_cases=n_cases,
        n_answered=n_answered,
        disease={k: rate(disease_hits[k], n_cases) for k in KS},
        gene={k: rate(gene_hits[k], n_gene) for k in KS},
    )


def summary_from_hits(
    disease_hits: dict[int, list[bool]], gene_hits: dict[int, list[bool]], n_answered: int
) -> Summary:
    """A Summary from per-case hits at each k. Gene lists hold only cases that have a gene."""
    return summary_from_counts(
        {k: sum(disease_hits[k]) for k in KS},
        len(disease_hits[KS[0]]),
        {k: sum(gene_hits[k]) for k in KS},
        len(gene_hits[KS[0]]),
        n_answered,
    )


def summarize(scores: list[CaseScore]) -> Summary:
    with_gene = [s for s in scores if s.has_gene]
    return summary_from_hits(
        {k: [found(s.disease_rank, k) for s in scores] for k in KS},
        {k: [found(s.gene_rank, k) for s in with_gene] for k in KS},
        sum(s.answered for s in scores),
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

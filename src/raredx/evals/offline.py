"""Offline evaluation of the parts that call no model: phenotype rankers and nominating
routes (chapter 32).

Every number here is computed on this machine: the rankers and the case bank run here,
and the model's own answer is read back from a recorded run. So a change to a ranker or
a route is measured on every development source for nothing, before a run that costs
money (docs/v2_design.md, section 5).

Two questions:
- rankers: with which similarity, which reordering of the top 30 and which knowledge
  does the no-model rank-then-check do best? Judged against the default by a rule fixed
  beforehand (PASS): no source significantly worse at first place or in the top ten,
  and at least two significantly better.
- routes: how often is the confirmed disease among the candidates the agent would see,
  for each mix of nominating routes?
"""

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from raredx.baselines.similar_patients import SimilarPatientsRank
from raredx.data.cases import Case
from raredx.evals import scoring
from raredx.evals.systems import question_of
from raredx.knowledge import masking
from raredx.knowledge.case_bank import CaseBank
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.rank_diseases import RankDiseases

POOL, DEEP, K = 30, 50, 60
BASELINE = ("OMIM", "F", "C")  # rank-then-check as it stands: funSimAvg, findings explained
Same = Callable[[str], Iterable[str]]


def rrf(*lists: list[str]) -> list[str]:
    """Reciprocal-rank fusion (k = 60): each list adds 1 / (k + place) to a disease."""
    score: dict[str, float] = defaultdict(float)
    for ranked in lists:
        for i, disease in enumerate(dict.fromkeys(ranked)):
            score[disease] += 1 / (K + i + 1)
    return [d for d, _ in sorted(score.items(), key=lambda x: (-x[1], x[0]))]


def first_rank(ranked: list[str], accepted: set[str], k: int = 10) -> int | None:
    return next((i for i, d in enumerate(ranked[:k], 1) if d in accepted), None)


def rankers(
    knowledge: dict[str, HPO], cases: dict[str, list[Case]], same: Same
) -> list[dict[str, Any]]:
    """For each knowledge, ranker (F funSimAvg, O one-way, FO their fusion) and order of
    the top 30 (N as ranked, C findings explained, I their information content): each
    case's rank of the confirmed disease in the top ten, or None."""
    rows: list[dict[str, Any]] = []
    for name, kb in knowledge.items():
        f_rank, o_rank = (
            RankDiseases(kb, "resnik", "funSimAvg"),
            RankDiseases(kb, "resnik", "oneway"),
        )
        check = CheckMatch(kb)
        information: dict[str, float] = {}
        for source, chosen in cases.items():
            for case in chosen:
                accepted = scoring.accepted_ids(case.disease_id, case.also_accepted, same)
                with masking.masked([case.pmid] if case.pmid else []):
                    f = [m.disease_id for m in f_rank(case.hpo_ids, top_k=DEEP).matches]
                    o = [m.disease_id for m in o_rank(case.hpo_ids, top_k=DEEP).matches]
                    pools = {"F": f[:POOL], "O": o[:POOL], "FO": rrf(f, o)[:POOL]}
                    weight: dict[str, tuple[int, float]] = {}
                    for disease in set().union(*pools.values()):
                        explained = check(case.hpo_ids, disease).explained
                        for e in explained:
                            if e.finding.hpo_id not in information:
                                information[e.finding.hpo_id] = kb.term(e.finding.hpo_id)[2]
                        total = sum(information[e.finding.hpo_id] for e in explained)
                        weight[disease] = (len(explained), total)
                for ranker, pool in pools.items():
                    orders = {
                        "N": pool,
                        "C": _reorder(pool, {d: weight[d][0] for d in pool}),
                        "I": _reorder(pool, {d: weight[d][1] for d in pool}),
                    }
                    for order, ranked in orders.items():
                        rows.append(
                            {
                                "knowledge": name,
                                "ranker": ranker,
                                "order": order,
                                "source": source,
                                "case_id": case.id,
                                "rank": first_rank(ranked, accepted),
                            }
                        )
    return rows


def _reorder(pool: list[str], weight: dict[str, float]) -> list[str]:
    """The pool by weight, highest first; ties keep the pool's order."""
    place = {d: i for i, d in enumerate(pool)}
    return sorted(pool, key=lambda d: (-weight[d], place[d]))


def paired(a: list[int | None], b: list[int | None], k: int) -> tuple[int, int]:
    """Cases only the first has in its top k, and only the second."""
    first = sum(
        (x is not None and x <= k) and not (y is not None and y <= k)
        for x, y in zip(a, b, strict=True)
    )
    second = sum(
        (y is not None and y <= k) and not (x is not None and x <= k)
        for x, y in zip(a, b, strict=True)
    )
    return first, second


def verdict(rows: list[dict[str, Any]], config: tuple[str, str, str]) -> dict[str, Any]:
    """The configuration against the baseline, per source: paired counts at first place
    and in the top ten, and whether it passes the rule fixed beforehand."""

    def ranks(cfg: tuple[str, str, str], source: str) -> list[int | None]:
        return [
            r["rank"]
            for r in rows
            if (r["knowledge"], r["ranker"], r["order"]) == cfg and r["source"] == source
        ]

    sources = sorted({r["source"] for r in rows}, key=[r["source"] for r in rows].index)
    out: dict[str, Any] = {"config": config, "sources": {}}
    worse = better = 0
    for source in sources:
        cells = {}
        improved = False
        for k in (1, 10):
            won, lost = paired(ranks(config, source), ranks(BASELINE, source), k)
            p = scoring.sign_test(won, lost)
            cells[k] = (won, lost, p)
            worse += p < 0.05 and lost > won
            improved |= p < 0.05 and won > lost
        better += improved
        out["sources"][source] = cells
    out["pass"] = worse == 0 and better >= 2
    return out


ROUTES = ("M", "F", "O", "C", "P")  # model, funSimAvg, one-way, case bank, similar patients


def routes(
    kb: HPO,
    cases: dict[str, list[Case]],
    same: Same,
    model_answers: dict[str, list[str]],
    bank: CaseBank | None,
    patients: SimilarPatientsRank | None,
) -> list[dict[str, Any]]:
    """Each case's top ten from every route (diseases as the knowledge names them, or as
    written when it has none), and whether each route has the confirmed disease."""
    f_rank, o_rank = RankDiseases(kb, "resnik", "funSimAvg"), RankDiseases(kb, "resnik", "oneway")
    rows: list[dict[str, Any]] = []
    for source, chosen in cases.items():
        for case in chosen:
            accepted = scoring.accepted_ids(case.disease_id, case.also_accepted, same)
            lists: dict[str, list[str]] = {}
            with masking.masked([case.pmid] if case.pmid else []):
                lists["F"] = [m.disease_id for m in f_rank(case.hpo_ids, top_k=10).matches]
                lists["O"] = [m.disease_id for m in o_rank(case.hpo_ids, top_k=10).matches]
                if patients is not None:
                    found = patients.predict(question_of(case))
                    lists["P"] = [c.disease_id for c in found if c.disease_id][:10]
            if case.id in model_answers:
                lists["M"] = model_answers[case.id][:10]
            if bank is not None:
                lists["C"] = bank.nominate(case.hpo_labels, case.pmid)
            rows.append(
                {
                    "source": source,
                    "case_id": case.id,
                    "lists": lists,
                    "hit": {r: any(d in accepted for d in lst) for r, lst in lists.items()},
                    "accepted": accepted,
                }
            )
    return rows


def coverage(rows: list[dict[str, Any]], mix: str) -> float | None:
    """Share of cases with the confirmed disease among the union of these routes' lists
    (e.g. "M+F+O"); None when a route of the mix is missing for the source."""
    parts = mix.split("+")
    usable = [r for r in rows if all(p in r["lists"] for p in parts)]
    if not usable or len(usable) < len(rows):
        return None
    found = sum(any(r["hit"][p] for p in parts) for r in usable)
    return found / len(usable)

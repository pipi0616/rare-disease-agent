"""Rank, then check: phenotype similarity proposes, the match check orders.

The two-stage shape of search and recommendation systems: a fast first stage
proposes candidates — tool T2's top 30 — and a closer look reorders them with
tool T4: the more of the patient's findings a disease explains, the higher;
ties keep T2's order. No model.

Chosen on dev-200: a pool of 30 beat 10 and 50; counting the findings
explained did as well as weighting them by rarity; contradictions changed no
order. It is the strongest baseline without a model, so the bar the agent
has to clear.
"""

from raredx.baselines.phenotype_rank import candidate
from raredx.evals.systems import Candidate, Question
from raredx.tools.check_match import CheckMatch
from raredx.tools.rank_diseases import RankDiseases

POOL = 30


class RankThenCheck:
    name = "rank-then-check"

    def __init__(self, rank: RankDiseases, check: CheckMatch, pool: int = POOL) -> None:
        self.rank = rank
        self.check = check
        self.pool = pool

    def params(self) -> dict[str, str]:
        return {
            "hpo_release": self.rank.hpo.release,
            "similarity": f"{self.rank.method}/{self.rank.combine}",
            "pool": str(self.pool),
            "order": "findings explained, then similarity",
        }

    def predict(self, question: Question) -> list[Candidate]:
        pool = self.rank(question.hpo_ids, top_k=self.pool).matches
        explained = [len(self.check(question.hpo_ids, m.disease_id).explained) for m in pool]
        order = sorted(range(len(pool)), key=lambda i: (-explained[i], i))
        return [candidate(pool[i]) for i in order[:10]]

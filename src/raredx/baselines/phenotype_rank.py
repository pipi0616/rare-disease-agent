"""B0 · the traditional baseline: rank diseases by phenotype similarity alone.

No model: the answer is tool T2's ranking as it stands. It is the bar the agent
has to clear, and it tells whether a model adds anything to a phenotype that is
already coded in HPO terms.
"""

from raredx.evals.systems import Candidate, Question
from raredx.tools.rank_diseases import COMBINE, METHOD, Match, RankDiseases


def candidate(match: Match) -> Candidate:
    """A ranked disease as an answer. A candidate names one gene; for a disease with
    several, it names none."""
    gene = match.genes[0] if len(match.genes) == 1 else None
    return Candidate(disease_name=match.disease_name, disease_id=match.disease_id, gene=gene)


class PhenotypeRank:
    def __init__(self, tool: RankDiseases) -> None:
        self.tool = tool
        default = (tool.method, tool.combine) == (METHOD, COMBINE)
        self.name = "phenotype-rank" if default else f"phenotype-rank ({self.similarity})"

    @property
    def similarity(self) -> str:
        return f"{self.tool.method}/{self.tool.combine}"

    def params(self) -> dict[str, str]:
        return {
            "hpo_release": self.tool.hpo.release,
            "similarity": self.similarity,
        }

    def predict(self, question: Question) -> list[Candidate]:
        return [candidate(m) for m in self.tool(question.hpo_ids, top_k=10).matches]

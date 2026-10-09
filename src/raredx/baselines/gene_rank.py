"""B0g · the genotype track's baseline: the candidate genes ranked by phenotype.

No model: tool T7 ranks the case's candidate genes by how well their diseases
match the phenotype, and the answer lists those diseases in that order, each
with its gene. It is what genotype adds without any reasoning, and the bar an
agent given the same genes has to clear.
"""

from raredx.evals.systems import Candidate, Question
from raredx.tools.rank_candidate_genes import RankCandidateGenes
from raredx.tools.rank_diseases import COMBINE, METHOD

K = 10


class GeneRank:
    name = "gene-rank"

    def __init__(self, tool: RankCandidateGenes) -> None:
        self.tool = tool

    def params(self) -> dict[str, str]:
        return {"hpo_release": self.tool.hpo.release, "similarity": f"{METHOD}/{COMBINE}"}

    def predict(self, question: Question) -> list[Candidate]:
        if not question.candidate_genes:
            raise ValueError("gene-rank needs candidate genes: run it with --with-genes")
        ranking = self.tool(question.hpo_ids, question.candidate_genes, top_k=50)
        candidates: list[Candidate] = []
        for match in ranking.genes:
            for disease in match.diseases:
                if all(c.disease_id != disease.disease_id for c in candidates):
                    candidates.append(
                        Candidate(
                            disease_name=disease.disease_name,
                            disease_id=disease.disease_id,
                            gene=match.gene,
                        )
                    )
        return candidates[:K]

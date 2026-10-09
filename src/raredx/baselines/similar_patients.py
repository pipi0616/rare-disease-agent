"""B0b · rank diseases by the most similar published patients alone.

No model: tool T5's patients, most similar first, read as diseases — each
disease in the order its nearest patient appears. It measures what the tool
finds on its own, beside B0 (the disease ranking), before an agent uses it.
"""

from raredx.evals.systems import Candidate, Question
from raredx.tools.find_similar_patients import FindSimilarPatients
from raredx.tools.rank_diseases import COMBINE, METHOD

K = 10


class SimilarPatientsRank:
    name = "similar-patients"

    def __init__(self, tool: FindSimilarPatients) -> None:
        self.tool = tool

    def params(self) -> dict[str, str]:
        return {
            "hpo_release": self.tool.hpo.release,
            "similarity": f"{METHOD}/{COMBINE}",
            "patient_bank": self.tool.bank_name,
        }

    def predict(self, question: Question) -> list[Candidate]:
        """The diseases of the nearest patients, each named once; the gene is the one
        found in its nearest patient."""
        candidates: list[Candidate] = []
        seen: set[str] = set()
        for case, _ in self.tool.ranked(question.hpo_ids)[0]:
            if case.disease_id in seen:
                continue
            seen.add(case.disease_id)
            candidates.append(
                Candidate(
                    disease_name=case.disease_label, disease_id=case.disease_id, gene=case.gene
                )
            )
            if len(candidates) == K:
                break
        return candidates

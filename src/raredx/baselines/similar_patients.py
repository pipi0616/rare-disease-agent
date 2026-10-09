"""B0b · rank diseases by the most similar published patients alone.

No model: tool T5's patients, most similar first, read as diseases — each
disease in the order its nearest patient appears. It measures what the tool
finds on its own, beside B0 (the disease ranking), before an agent uses it.

What it reads is recorded as a tool span, like every other system's tool
calls, so the evaluation's leak audit sees it.
"""

import mlflow
from mlflow.entities import SpanType

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

    @mlflow.trace(name="find_similar_patients", span_type=SpanType.TOOL)
    def nearest(self, hpo_ids: list[str]) -> list[dict[str, str | None]]:
        """The nearest patients, most similar first, until K diseases are named: each
        patient's diagnosis, gene and paper — what the leak audit reads."""
        read: list[dict[str, str | None]] = []
        diseases: set[str] = set()
        for case, _ in self.tool.ranked(hpo_ids)[0]:
            read.append(
                {
                    "disease_id": case.disease_id,
                    "disease_name": case.disease_label,
                    "gene": case.gene,
                    "source": case.pmid,
                }
            )
            diseases.add(case.disease_id)
            if len(diseases) == K:
                break
        return read

    def predict(self, question: Question) -> list[Candidate]:
        """The diseases of the nearest patients, each named once; the gene is the one
        found in its nearest patient."""
        candidates: list[Candidate] = []
        for patient in self.nearest(question.hpo_ids):
            if all(c.disease_id != patient["disease_id"] for c in candidates):
                candidates.append(
                    Candidate(
                        disease_name=patient["disease_name"] or "",
                        disease_id=patient["disease_id"],
                        gene=patient["gene"],
                    )
                )
        return candidates

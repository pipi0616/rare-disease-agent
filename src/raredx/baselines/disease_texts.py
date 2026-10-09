"""B0c · rank diseases by the disease texts that best match the patient's findings.

No model: the patient's findings, written out as words, are the query to tool
T6. Each of the best passages gives credit to the diseases it is about, by
reciprocal rank, shared among them: a passage about one disease credits it
fully, a MedlinePlus condition covering thirty subtypes credits each a
thirtieth. It measures the text retrieval on its own, beside B0 and B0b.

What it reads is recorded as a tool span, so the leak audit sees it.
"""

from collections import defaultdict

import mlflow
from mlflow.entities import SpanType

from raredx.evals.systems import Candidate, Question
from raredx.knowledge.texts import Passage
from raredx.tools.search_disease_texts import SearchDiseaseTexts

K = 10
PASSAGES = 50  # passages read
RRF_K = 60  # the usual constant of reciprocal-rank fusion


class DiseaseTextsRank:
    name = "disease-texts"

    def __init__(self, tool: SearchDiseaseTexts) -> None:
        self.tool = tool

    def params(self) -> dict[str, str]:
        info = self.tool.index.info
        return {
            "hpo_release": self.tool.hpo.release,
            "text_index": f"{info['sources']}; {info['passages']} passages",
            "retrieval": f"hybrid: {info['dense']} + {info['sparse']}, RRF",
            "ranking": f"top {PASSAGES} passages, reciprocal-rank credit shared among a "
            "passage's diseases",
        }

    @mlflow.trace(name="search_disease_texts", span_type=SpanType.TOOL)
    def passages(self, query: str) -> list[Passage]:
        return self.tool.ranked(query, PASSAGES)

    def predict(self, question: Question) -> list[Candidate]:
        credit: dict[str, float] = defaultdict(float)
        for rank, passage in enumerate(self.passages("; ".join(question.hpo_labels))):
            for disease in passage.disease_ids:
                credit[disease] += 1 / (RRF_K + rank) / len(passage.disease_ids)
        candidates = []
        for disease in sorted(credit, key=lambda d: (-credit[d], d))[:K]:
            genes = self.tool.hpo.genes.get(disease, ())
            candidates.append(
                Candidate(
                    disease_name=self.tool.hpo.names.get(disease, disease),
                    disease_id=disease,
                    gene=genes[0] if len(genes) == 1 else None,
                )
            )
        return candidates

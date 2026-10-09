"""B0c · rank diseases by the disease texts that best match the patient's findings.

No model: the patient's findings, written out as words, are the query to tool
T6; each disease is placed where its first passage comes. It measures the text
retrieval on its own, beside B0 and B0b, before an agent uses it.
"""

from raredx.evals.systems import Candidate, Question
from raredx.tools.search_disease_texts import SearchDiseaseTexts

K = 10
PASSAGES = 50  # passages read to collect K diseases


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
        }

    def predict(self, question: Question) -> list[Candidate]:
        diseases: list[str] = []
        for passage in self.tool.ranked("; ".join(question.hpo_labels), PASSAGES):
            for disease in passage.disease_ids:
                if disease not in diseases:
                    diseases.append(disease)
        candidates = []
        for disease in diseases[:K]:
            genes = self.tool.hpo.genes.get(disease, ())
            candidates.append(
                Candidate(
                    disease_name=self.tool.hpo.names.get(disease, disease),
                    disease_id=disease,
                    gene=genes[0] if len(genes) == 1 else None,
                )
            )
        return candidates

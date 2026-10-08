"""T2 · rank diseases by phenotype: the traditional method, as a tool.

Every OMIM disease in the HPO release is scored by how closely its annotated
phenotype matches the patient's, and the best are returned. The score follows
the standard approach of phenotype-driven diagnosis (Phenomizer; Köhler et
al., 2009), computed by hpo3:

- a term counts by its information content: the fewer diseases show it, the
  more a match on it says ("Seizure" is everywhere, "Ectopia lentis" is not);
- two different terms match as far as they share an ancestor in the ontology,
  scored by that ancestor's information content (Resnik);
- each patient term takes its best match among the disease's terms, each
  disease term its best among the patient's, and the two averages are
  averaged (funSimAvg; Phenomizer's original form used the first direction).

Resnik with funSimAvg scored best of hpo3's measures on dev-200, with each
case's source paper masked.
"""

from typing import Annotated

import mlflow
from mlflow.entities import SpanType
from pydantic import BaseModel, Field, validate_call

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.ids import HpoId

# hpo3's term similarity measures, and its ways of combining them into a set similarity.
METHODS = ("resnik", "lin", "jc", "jc2", "rel", "ic", "graphic", "dist")
COMBINES = ("funSimAvg", "funSimMax", "BMA")
METHOD, COMBINE = "resnik", "funSimAvg"  # the default; see above for why


class Match(BaseModel):
    disease_id: str = Field(description="OMIM id, e.g. OMIM:619340")
    disease_name: str
    genes: list[str] = Field(description="Genes known to cause it (Mendelian), if any")
    score: float = Field(description="Phenotype similarity; compare within one ranking only")


class Ranking(BaseModel):
    matches: list[Match] = Field(description="Best match first")
    unrecognized: list[str] = Field(
        description="Input terms this HPO release does not know; they were left out"
    )
    hpo_release: str


class RankDiseases:
    name = "rank_diseases"
    title = "Rank diseases by phenotype"

    def __init__(self, hpo: HPO, method: str = METHOD, combine: str = COMBINE) -> None:
        if method not in METHODS or combine not in COMBINES:
            raise ValueError(
                f"unknown similarity {method}/{combine}: the method is one of "
                f"{', '.join(METHODS)}; the combination one of {', '.join(COMBINES)}"
            )
        self.hpo = hpo
        self.method = method
        self.combine = combine

    @mlflow.trace(name="rank_diseases", span_type=SpanType.TOOL)
    @validate_call
    def __call__(
        self,
        hpo_ids: Annotated[
            list[HpoId],
            Field(min_length=1, description="The patient's phenotype as HPO term ids"),
        ],
        top_k: Annotated[int, Field(ge=1, le=50, description="How many diseases to return")] = 10,
    ) -> Ranking:
        """Rank every OMIM disease by how well its known phenotype matches the patient's.

        Use it on the patient's HPO terms to get candidate diagnoses. It knows only
        what HPO has annotated: a disease with few annotations ranks low whatever
        it is, and a score is not a probability.
        """
        patient, unrecognized = self.hpo.patient(hpo_ids)
        matches: list[Match] = []
        if len(patient):
            profiles = self.hpo.profiles(masking.current())
            scores = patient.similarity_scores(
                profiles, kind="omim", method=self.method, combine=self.combine
            )
            ids = self.hpo.disease_ids
            order = sorted(range(len(ids)), key=lambda i: (-scores[i], ids[i]))
            matches = [
                Match(
                    disease_id=ids[i],
                    disease_name=self.hpo.names[ids[i]],
                    genes=list(self.hpo.genes.get(ids[i], ())),
                    score=round(scores[i], 3),
                )
                for i in order[:top_k]
                if scores[i] > 0
            ]
        return Ranking(matches=matches, unrecognized=unrecognized, hpo_release=self.hpo.release)

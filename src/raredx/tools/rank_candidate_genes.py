"""T7 · rank candidate genes: which of the sequenced genes explains the phenotype.

Sequencing leaves a list of candidate genes; the question is which of them
causes the patient's disease. For each gene, the diseases it is known to cause
(HPO's Mendelian gene–disease associations) are scored against the patient's
phenotype with the disease ranking's similarity, and the gene takes its best
disease's score. This is the phenotype half of what clinical tools such as
Exomiser do; the variant half (frequency, predicted damage) is not modelled.

A gene with no known disease is listed apart: it may still be causal — a new
disease — but nothing can be scored for it. While a paper is masked, a disease
known only from that paper does not exist, as for every tool: its gene then
counts as one with no known disease. In evaluation that is the case's own
paper, which in such cases is also where the gene–disease link was reported.
"""

from typing import Annotated

import mlflow
from mlflow.entities import SpanType
from pydantic import BaseModel, Field, StringConstraints, validate_call

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.ids import HpoId
from raredx.tools.rank_diseases import COMBINE, METHOD

GeneSymbol = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,19}$")]
MAX_DISEASES = 3  # per gene, best first


class GeneDisease(BaseModel):
    disease_id: str
    disease_name: str
    score: float = Field(description="Phenotype similarity; compare within one ranking only")


class GeneMatch(BaseModel):
    gene: str
    best_score: float
    diseases: list[GeneDisease] = Field(description="The gene's diseases, best match first")
    n_diseases: int = Field(description="All its known diseases; more than listed when cut")


class GeneRanking(BaseModel):
    genes: list[GeneMatch] = Field(description="Best-matching gene first")
    no_known_disease: list[str] = Field(
        description="Candidate genes with no known disease: possibly causal, but not scorable"
    )
    unrecognized: list[str] = Field(description="Input HPO terms this release does not know")


class RankCandidateGenes:
    name = "rank_candidate_genes"
    title = "Rank candidate genes by phenotype"

    def __init__(self, hpo: HPO) -> None:
        self.hpo = hpo

    @mlflow.trace(name="rank_candidate_genes", span_type=SpanType.TOOL)
    @validate_call
    def __call__(
        self,
        hpo_ids: Annotated[
            list[HpoId],
            Field(min_length=1, description="The patient's phenotype as HPO term ids"),
        ],
        genes: Annotated[
            list[GeneSymbol],
            Field(min_length=1, max_length=500, description="Candidate genes from sequencing"),
        ],
        top_k: Annotated[int, Field(ge=1, le=50, description="How many genes to return")] = 10,
    ) -> GeneRanking:
        """Rank the patient's candidate genes from sequencing by how well the diseases
        each is known to cause match the phenotype.

        Use it when the patient has candidate genes. Genes with no known disease are
        listed apart: one may still be causal, but cannot be scored.
        """
        patient, unrecognized = self.hpo.patient(hpo_ids)
        hidden = self.hpo.known_only_from(masking.current())
        scores: dict[str, float] = {}
        if len(patient):
            profiles = self.hpo.profiles(masking.current())
            values = patient.similarity_scores(
                profiles, kind="omim", method=METHOD, combine=COMBINE
            )
            scores = dict(zip(self.hpo.disease_ids, values, strict=True))
        matched: list[GeneMatch] = []
        no_known: list[str] = []
        for gene in dict.fromkeys(genes):  # each once, in the order given
            diseases = [d for d in self.hpo.diseases_of_gene.get(gene, ()) if d not in hidden]
            if not diseases:
                no_known.append(gene)
                continue
            ranked = sorted(diseases, key=lambda d: (-scores.get(d, 0.0), d))
            matched.append(
                GeneMatch(
                    gene=gene,
                    best_score=round(scores.get(ranked[0], 0.0), 3),
                    diseases=[
                        GeneDisease(
                            disease_id=d,
                            disease_name=self.hpo.names[d],
                            score=round(scores.get(d, 0.0), 3),
                        )
                        for d in ranked[:MAX_DISEASES]
                    ],
                    n_diseases=len(ranked),
                )
            )
        matched.sort(key=lambda m: (-m.best_score, m.gene))
        return GeneRanking(
            genes=matched[:top_k], no_known_disease=sorted(no_known), unrecognized=unrecognized
        )

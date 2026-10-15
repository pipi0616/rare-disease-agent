"""T5 · find similar patients: published cases whose phenotype resembles the patient's.

The other tools compare the patient with diseases: each disease's annotated
profile, pooled from its reports. This one compares the patient with patients
— the individual cases of Phenopacket Store, each with a confirmed diagnosis —
and returns the closest, with their diagnoses. Clinicians do the same when they
look for "a case like this one" in the literature (PubCaseFinder, case-based
reasoning).

It finds what the disease ranking misses. Of agent-v3's dev-200 cases whose
right disease no tool ever showed, most were annotated in HPO but ranked far
down; for many, other papers had reported patients with the same disease.

The similarity is the disease ranking's (Resnik, funSimAvg), between two
patients' terms. Patients from a masked paper are left out: in evaluation the
case's own paper, so neither the case nor anyone reported with it is found. So
are patients of a disease HPO knows only from a masked paper, as for every tool.
What the bank holds is the caller's choice; evaluation gives it the design
split only, so the heldout cases stay unseen until the final run.
"""

from typing import Annotated

import mlflow
from mlflow.entities import SpanType
from pydantic import BaseModel, Field, validate_call

from raredx.data.cases import Case
from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.ids import HpoId
from raredx.tools.rank_diseases import COMBINE, METHOD


class SimilarPatient(BaseModel):
    disease_id: str = Field(description="The patient's confirmed diagnosis, an OMIM id")
    disease_name: str
    similarity: float = Field(description="Phenotype similarity; compare within one search only")
    shared: list[str] = Field(
        description="Your patient's findings this patient also had: the same term, or one "
        "a more specific kind of the other"
    )
    source: str | None = Field(description="The paper that reported the patient")


class SimilarPatients(BaseModel):
    patients: list[SimilarPatient] = Field(description="Most similar first")
    searched: int = Field(description="Published patients searched")
    unrecognized: list[str] = Field(
        description="Input terms this HPO release does not know; they were left out"
    )


class FindSimilarPatients:
    name = "find_similar_patients"
    title = "Find similar published patients"

    def __init__(self, hpo: HPO, bank: list[Case], bank_name: str) -> None:
        self.hpo = hpo
        self.bank = bank
        self.bank_name = bank_name
        self._sets = [hpo.patient(c.hpo_ids)[0] for c in bank]
        self._index = {c.id: i for i, c in enumerate(bank)}

    def ranked(self, hpo_ids: list[str]) -> tuple[list[tuple[Case, float]], list[str]]:
        """Every unmasked patient with any similarity, most similar first (ties by case
        id), and the input terms this release does not know."""
        patient, unrecognized = self.hpo.patient(hpo_ids)
        if not len(patient):
            return [], unrecognized
        masked = masking.current()
        hidden = self.hpo.known_only_from(masked)
        scores = patient.similarity_scores(self._sets, kind="omim", method=METHOD, combine=COMBINE)
        found = [
            (case, score)
            for case, score in zip(self.bank, scores, strict=True)
            if score > 0 and case.pmid not in masked and case.disease_id not in hidden
        ]
        found.sort(key=lambda x: (-x[1], x[0].id))
        return found, unrecognized

    @mlflow.trace(name="find_similar_patients", span_type=SpanType.TOOL)
    @validate_call
    def __call__(
        self,
        hpo_ids: Annotated[
            list[HpoId],
            Field(min_length=1, description="The patient's phenotype as HPO term ids"),
        ],
        top_k: Annotated[int, Field(ge=1, le=50, description="How many patients to return")] = 10,
    ) -> SimilarPatients:
        """Find published patients whose phenotype resembles this patient's, each with
        their confirmed diagnosis.

        Use it beside rank_diseases: it compares the patient with individual reported
        patients rather than with diseases' pooled profiles, so it can find a disease
        the ranking missed. A disease several similar patients share is a candidate.
        """
        found, unrecognized = self.ranked(hpo_ids)
        findings = [str(term.id) for term in self.hpo.patient(hpo_ids)[0]]
        masked = masking.current()
        hidden = self.hpo.known_only_from(masked)
        return SimilarPatients(
            patients=[
                SimilarPatient(
                    disease_id=case.disease_id,
                    disease_name=case.disease_label,
                    similarity=round(score, 3),
                    shared=self._shared(findings, case),
                    source=case.pmid,
                )
                for case, score in found[:top_k]
            ],
            searched=sum(
                case.pmid not in masked and case.disease_id not in hidden for case in self.bank
            ),
            unrecognized=unrecognized,
        )

    def _shared(self, findings: list[str], case: Case) -> list[str]:
        """The findings the other patient also had, as labels: the same term, or one a
        kind of the other."""
        theirs = [str(term.id) for term in self._sets[self._index[case.id]]]
        return [
            self.hpo.term(f)[1] for f in findings if any(self.hpo.relation(f, t) for t in theirs)
        ]

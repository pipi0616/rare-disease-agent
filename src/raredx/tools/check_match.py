"""T4 · check a match: the patient's findings against one disease, item by item.

For each of the patient's findings, whether the disease explains it — the same
term, or one is a more specific kind of the other in the ontology — and if
not, whether the disease's sources recorded it as absent (a contradiction).
And the other way round: the disease's features seen in at least half of its
reported patients that the patient does not have.

A model reading two lists of terms cannot reliably tell that "Bilateral
sensorineural hearing impairment" is a kind of "Hearing impairment"; the
ontology can. So the comparison is computed here and handed to the model.

Lines resting only on a masked source are left out, as everywhere else.
"""

from typing import Annotated

import mlflow
from mlflow.entities import SpanType
from pydantic import BaseModel, Field, validate_call

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO, Feature, Relation
from raredx.tools.ids import DiseaseId, HpoId, require_disease

MISSING_FROM = 0.5  # a feature counts as missing when at least this share of patients have it
MAX_MISSING = 10


class Finding(BaseModel):
    hpo_id: str
    label: str


class Explained(BaseModel):
    finding: Finding
    feature: str = Field(description="The disease's feature that explains it")
    relation: Relation = Field(
        description="How the finding stands to the feature: the same term, a more specific "
        "kind of it, or a less specific one"
    )
    frequency: str | None = Field(description="How often the disease's patients show it")
    sources: list[str]


class Contradicted(BaseModel):
    finding: Finding
    feature: str = Field(description="The feature the disease's sources recorded as absent")
    frequency: str = Field(description="e.g. 0/3: looked for in 3 patients, found in none")
    sources: list[str]


class Missing(BaseModel):
    feature: Finding
    frequency: str
    sources: list[str]


class MatchReport(BaseModel):
    disease_id: str
    disease_name: str
    n_findings: int = Field(description="The patient's findings compared")
    explained: list[Explained]
    unexplained: list[Finding] = Field(description="Findings the disease does not explain")
    contradicted: list[Contradicted] = Field(
        description="Findings the disease's sources looked for and did not find"
    )
    missing: list[Missing] = Field(
        description="Features seen in at least half of the disease's reported patients that "
        "the patient does not have; most frequent first"
    )
    n_missing: int = Field(description="All such features; more than len(missing) when cut")
    unrecognized: list[str] = Field(description="Input terms this HPO release does not know")
    hpo_release: str


class CheckMatch:
    name = "check_match"
    title = "Check a disease against the patient"

    def __init__(self, hpo: HPO) -> None:
        self.hpo = hpo

    @mlflow.trace(name="check_match", span_type=SpanType.TOOL)
    @validate_call
    def __call__(
        self,
        hpo_ids: Annotated[
            list[HpoId],
            Field(min_length=1, description="The patient's phenotype as HPO term ids"),
        ],
        disease_id: Annotated[
            DiseaseId, Field(description="A disease id (OMIM or ORPHA) as rank_diseases returns it")
        ],
    ) -> MatchReport:
        """Compare the patient's findings with one disease: which it explains, which it
        does not, which its sources found absent, and which of its frequent features the
        patient lacks.

        Use it to weigh a candidate from rank_diseases against the patient.
        """
        disease_id = require_disease(self.hpo, disease_id)
        patient, unrecognized = self.hpo.patient(hpo_ids)
        findings = [self._finding(str(term.id)) for term in patient]
        features = self.hpo.features(disease_id, masking.current())
        seen = [f for f in features if not f.absent]
        ruled_out = [f for f in features if f.absent]

        explained, unexplained, contradicted = [], [], []
        for finding in findings:
            match = self._best(finding.hpo_id, seen)
            if match is not None:
                feature, relation = match
                explained.append(
                    Explained(
                        finding=finding,
                        feature=feature.label,
                        relation=relation,
                        frequency=feature.frequency.text,
                        sources=sorted(feature.sources),
                    )
                )
                continue
            against = [
                f
                for f in ruled_out
                if self.hpo.relation(finding.hpo_id, f.term) in ("same", "more specific")
            ]
            if against:
                feature = max(against, key=lambda f: f.information)
                contradicted.append(
                    Contradicted(
                        finding=finding,
                        feature=feature.label,
                        frequency=feature.frequency.text or "0",
                        sources=sorted(feature.sources),
                    )
                )
            else:
                unexplained.append(finding)

        missing = [
            f
            for f in seen
            if (f.frequency.fraction or 0.0) >= MISSING_FROM
            and not any(self.hpo.relation(x.hpo_id, f.term) for x in findings)
        ]
        missing.sort(key=lambda f: (-(f.frequency.fraction or 0.0), -f.information, f.term))
        return MatchReport(
            disease_id=disease_id,
            disease_name=self.hpo.names[disease_id],
            n_findings=len(findings),
            explained=explained,
            unexplained=unexplained,
            contradicted=contradicted,
            missing=[
                Missing(
                    feature=Finding(hpo_id=f.term, label=f.label),
                    frequency=f.frequency.text or "",
                    sources=sorted(f.sources),
                )
                for f in missing[:MAX_MISSING]
            ],
            n_missing=len(missing),
            unrecognized=unrecognized,
            hpo_release=self.hpo.release,
        )

    def _finding(self, hpo_id: str) -> Finding:
        term, label, _ = self.hpo.term(hpo_id)
        return Finding(hpo_id=term, label=label)

    def _best(self, finding: str, features: list[Feature]) -> tuple[Feature, Relation] | None:
        """The feature that explains the finding best: the same term first, then the most
        specific feature the finding is a kind of, then the most specific one below it."""
        order = {"same": 0, "more specific": 1, "less specific": 2}
        matches = [(f, r) for f in features if (r := self.hpo.relation(finding, f.term))]
        if not matches:
            return None
        return min(matches, key=lambda m: (order[m[1]], -m[0].information, m[0].term))

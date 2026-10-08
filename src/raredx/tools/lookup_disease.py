"""T3 · look up a disease: what HPO records about it, sized for a model to read.

For one OMIM disease: its features with how often patients show them, its
inheritance, onset and course, its genes, and the sources all of it was
curated from — the evidence an answer can cite.

A tool's answer goes into the model's context, so it is kept to what helps:
the most frequent features first (the more specific first among equals),
features without a recorded frequency after them, and at most max_features of
them, with the total stated, so the model knows when there is more to ask for.
A disease can carry over 200 annotated features; most carry about a dozen.

Lines resting only on a masked source are left out, as everywhere else. The
answer never says that anything was masked.
"""

from typing import Annotated

import mlflow
from mlflow.entities import SpanType
from pydantic import BaseModel, Field, StringConstraints, validate_call

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO, absent, frequency

OmimId = Annotated[str, StringConstraints(pattern=r"^OMIM:\d{6}$")]


class UnknownDisease(LookupError):
    """The id is well formed, but this HPO release has no such disease."""


class Feature(BaseModel):
    hpo_id: str
    label: str
    frequency: str | None = Field(
        description="How often reported patients show it, e.g. 4/8 or frequent (30–79%); "
        "null when no source says"
    )
    sources: list[str]


class DiseaseProfile(BaseModel):
    disease_id: str
    disease_name: str
    genes: list[str] = Field(description="Genes known to cause it (Mendelian)")
    inheritance: list[str]
    onset_and_course: list[str] = Field(description="e.g. Childhood onset, Progressive")
    features: list[Feature] = Field(
        description="Most frequent first; features with no recorded frequency last"
    )
    n_features: int = Field(
        description="How many features HPO records in all; more than len(features) when "
        "the list was cut at max_features. 0: HPO records no phenotype for this disease"
    )
    sources: list[str] = Field(description="Every source these annotations were curated from")
    hpo_release: str


class LookupDisease:
    name = "lookup_disease"

    def __init__(self, hpo: HPO) -> None:
        self.hpo = hpo

    @mlflow.trace(name="lookup_disease", span_type=SpanType.TOOL)
    @validate_call
    def __call__(
        self,
        disease_id: Annotated[
            OmimId, Field(description="An OMIM disease id as rank_diseases returns it")
        ],
        max_features: Annotated[
            int, Field(ge=1, le=300, description="How many features to return at most")
        ] = 20,
    ) -> DiseaseProfile:
        """Look up one disease: its features and how often patients show them, its
        inheritance, onset, genes, and the sources behind all of it.

        Use it to check a candidate from rank_diseases against the patient.
        """
        if disease_id not in self.hpo.names:
            raise UnknownDisease(
                f"{disease_id} is not a disease in HPO {self.hpo.release}; "
                "use an id that rank_diseases returned"
            )
        masked = masking.current()
        by_term: dict[str, list[str]] = {}  # feature -> its frequencies as written
        cited: dict[str, set[str]] = {}
        sources: set[str] = set()
        for line in self.hpo.lines(disease_id, "P", masked):
            by_term.setdefault(line.term, []).append(line.frequency)
            cited.setdefault(line.term, set()).update(line.refs)
            sources |= line.refs
        features: list[tuple[float | None, float, Feature]] = []
        for term, written in by_term.items():
            if all(absent(w) for w in written):
                continue  # looked for, never found: not a feature of the disease
            hpo_id, label, information = self.hpo.term(term)
            freq = frequency(written)
            feature = Feature(
                hpo_id=hpo_id, label=label, frequency=freq.text, sources=sorted(cited[term])
            )
            features.append((freq.fraction, information, feature))
        features.sort(key=lambda f: (f[0] is None, -(f[0] or 0.0), -f[1], f[2].hpo_id))
        inheritance = self.hpo.lines(disease_id, "I", masked)
        course = self.hpo.lines(disease_id, "C", masked)
        for line in (*inheritance, *course):
            sources |= line.refs
        return DiseaseProfile(
            disease_id=disease_id,
            disease_name=self.hpo.names[disease_id],
            genes=list(self.hpo.genes.get(disease_id, ())),
            inheritance=sorted({self.hpo.term(line.term)[1] for line in inheritance}),
            onset_and_course=sorted({self.hpo.term(line.term)[1] for line in course}),
            features=[f for _, _, f in features[:max_features]],
            n_features=len(features),
            sources=sorted(sources),
            hpo_release=self.hpo.release,
        )

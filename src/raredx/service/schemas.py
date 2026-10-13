"""What the service takes and returns: the API's contract.

A request is coded data only — HPO term ids, sex, gene symbols, PubMed ids —
each checked against a pattern, and any other field is refused. There is no
free-text field, so a name, a date of birth or a clinical note cannot be sent
by mistake: what never enters cannot reach a log, a trace or the model provider.

An answer says how it was produced: by the agent or by the fallback, with which
model, prompt and knowledge, and under which trace the whole of it is recorded.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from raredx.tools.check_match import MatchReport
from raredx.tools.ids import HpoId

MAX_TERMS = 100  # the longest case in Phenopacket Store 0.1.27 has 66
MAX_GENES = 200  # a filtered exome leaves tens of candidates
MAX_EXCLUDED = 20

GeneSymbol = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9.-]{0,24}$")]
Pmid = Annotated[str, StringConstraints(pattern=r"^PMID:\d{1,9}$")]
Sex = Literal["female", "male", "unknown"]

DISCLAIMER = (
    "Research software, not a medical device: a ranked list of hypotheses with their "
    "evidence, for a clinical geneticist to weigh — never a diagnosis on its own."
)


class DiagnoseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hpo_ids: list[HpoId] = Field(
        min_length=1,
        max_length=MAX_TERMS,
        description="The patient's findings as HPO term ids",
        examples=[["HP:0000407", "HP:0000510", "HP:0001250"]],
    )
    sex: Sex = "unknown"
    candidate_genes: list[GeneSymbol] | None = Field(
        default=None,
        max_length=MAX_GENES,
        description="Genes left after filtering the patient's sequencing, if it was done",
    )
    exclude_sources: list[Pmid] = Field(
        default_factory=list,
        max_length=MAX_EXCLUDED,
        description="Publications to leave out of the knowledge used — for a patient who "
        "was published: with their own report in, the answer is read, not reasoned",
    )


class Finding(BaseModel):
    hpo_id: str
    label: str
    given_as: str | None = Field(
        default=None, description="The obsolete id that was sent, when this term replaced it"
    )


class Evidence(BaseModel):
    """What the knowledge says about one diagnosis against this patient: the tools' own
    output, computed for the answer whether or not the agent asked for it."""

    match: MatchReport
    inheritance: list[str]
    onset_and_course: list[str]
    genes: list[str]
    sources: list[str] = Field(description="Every source the disease's annotations cite")


class Diagnosis(BaseModel):
    rank: int
    disease_id: str
    disease_name: str
    gene: str | None = None
    reason: str | None = Field(description="Why it stands here, in the agent's words")
    evidence: Evidence | None = Field(
        description="Null when HPO has no annotation of the disease to check against"
    )


StepKind = Literal["tools", "model", "tool", "answer", "fallback"]


class Step(BaseModel):
    """One thing the system did, as it is shown to someone watching."""

    n: int
    kind: StepKind
    title: str
    detail: str | None = None
    seconds: float = Field(description="Since the request started")


class Usage(BaseModel):
    seconds: float
    model_calls: int = 0
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    cost_usd_estimate: float = Field(default=0.0, description="At the provider's peak price")


class SystemInfo(BaseModel):
    """What is serving: enough to tie an answer to the version that was evaluated."""

    service_version: str
    code: str
    model_available: bool
    unavailable_because: str | None = None
    agent: dict[str, Any] | None = Field(
        description="The agent's configuration, as an evaluation run records it"
    )
    agent_with_genes: dict[str, Any] | None
    fallback: dict[str, Any]
    limits: dict[str, Any]


Mode = Literal["agent", "fallback"]


class DiagnoseResponse(BaseModel):
    request_id: str
    mode: Mode
    fallback_reason: str | None = None
    findings: list[Finding]
    diagnoses: list[Diagnosis]
    steps: list[Step]
    usage: Usage
    trace_id: str | None = Field(description="The MLflow trace holding every call made for it")
    system: SystemInfo
    disclaimer: str = DISCLAIMER


class Term(BaseModel):
    hpo_id: str
    label: str


class Example(BaseModel):
    """A published patient to try the service on, with the diagnosis its paper confirmed."""

    id: str
    title: str
    request: DiagnoseRequest
    findings: list[Finding]
    candidate_genes: list[str] | None = Field(
        description="Simulated sequencing, as in the evaluation: the causal gene among decoys"
    )
    confirmed_disease_id: str
    confirmed_disease_name: str
    confirmed_gene: str | None
    source: str
    in_evaluation: str = Field(description="What the held-out evaluation recorded for it")


class Problem(BaseModel):
    """The body of an error response."""

    detail: Any
    request_id: str | None = None

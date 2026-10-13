"""One request, start to finish: the evaluated agent — or, when the model cannot be
reached, the ranking that needs no model, and the answer says which.

What answers is what was measured. A request without candidate genes goes to
the agent of the phenotype track; one with them, to the agent of the genotype
track; each is built exactly as the evaluation built it, and its `predict` is
called unchanged.

The no-model ranking is computed first, for every request. It takes a fraction
of a second, it is the first thing a watching client sees, and it is the answer
if the model fails: no key, an API error, no final answer, the deadline. A
service that depends on someone else's API will see that API fail; what it
answers then is decided here, and was measured too (rank-then-check and
gene-rank, both evaluated on the held-out set). A failure of our own code is
not papered over the same way: it is raised, and the caller gets an error.

Every request is one MLflow trace, shaped like an evaluation's: the question in,
the candidates out, each tool and model call a span inside. A request can so be
read, replayed and judged with the tools built for evaluation runs.
"""

import threading
import time
from collections.abc import Callable
from importlib.metadata import version
from typing import Any

import mlflow
import openai
from mlflow.entities import SpanType
from pydantic import ValidationError

from raredx.agent import FILLED, FUSED, Agent, NoFinalAnswer
from raredx.baselines.gene_rank import GeneRank
from raredx.baselines.phenotype_rank import candidate
from raredx.baselines.rank_then_check import RankThenCheck
from raredx.evals.systems import Candidate, Question
from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.service.schemas import (
    MAX_GENES,
    MAX_TERMS,
    DiagnoseRequest,
    DiagnoseResponse,
    Diagnosis,
    Evidence,
    Finding,
    Mode,
    Step,
    StepKind,
    SystemInfo,
    Usage,
)
from raredx.service.steps import describe
from raredx.service.watch import Cancelled, DeadlineExceeded, Event, Watcher, watching
from raredx.tools.check_match import CheckMatch
from raredx.tools.ids import UnknownDisease
from raredx.tools.lookup_disease import LookupDisease
from raredx.tools.rank_candidate_genes import RankCandidateGenes
from raredx.tools.rank_diseases import RankDiseases

# Sex as Phenopacket Store writes it: what the prompts of the evaluation showed.
SEX = {"female": "FEMALE", "male": "MALE", "unknown": "UNKNOWN_SEX"}
LEADING = 3


class UnknownTerms(ValueError):
    """Well-formed HPO ids that the loaded release does not have."""

    def __init__(self, terms: list[str], release: str) -> None:
        super().__init__(f"not HPO terms in release {release}: {', '.join(terms)}")
        self.terms = terms


class NoFinding(ValueError):
    """None of the terms describes a finding (all are modifiers, onset or inheritance)."""


class _Steps:
    """The steps of one request, numbered and timed as they are added — from several
    threads at once when a turn's tool calls run in parallel."""

    def __init__(self, started: float, on_step: Callable[[Step], None] | None) -> None:
        self.started = started
        self.on_step = on_step
        self.steps: list[Step] = []
        self._lock = threading.Lock()

    def add(self, kind: StepKind, title: str, detail: str | None = None) -> None:
        with self._lock:  # numbered and handed on in one order
            step = Step(
                n=len(self.steps) + 1,
                kind=kind,
                title=title,
                detail=detail,
                seconds=round(time.monotonic() - self.started, 2),
            )
            self.steps.append(step)
            if self.on_step is not None:
                self.on_step(step)

    def event(self, event: Event) -> None:
        self.add(*describe(event))


class Diagnoser:
    def __init__(
        self,
        hpo: HPO,
        *,
        agent: Agent | None,
        agent_with_genes: Agent | None,
        unavailable_because: str | None = None,
        deadline_seconds: float = 60.0,
        prices: tuple[float, float, float] = (0.0, 0.0, 0.0),
        code: str = "unknown",
    ) -> None:
        """`agent` answers requests without candidate genes, `agent_with_genes` those
        with; None for both serves the fallback only, and `unavailable_because` says
        why. `prices` are USD per million tokens: input, cached input, output."""
        if (agent is None) != (agent_with_genes is None):
            raise ValueError("give both agents, or neither")
        self.hpo = hpo
        self.agent = agent
        self.agent_with_genes = agent_with_genes
        self.unavailable_because: str | None = None
        if agent is None:
            self.unavailable_because = unavailable_because or "no model is configured"
        self.deadline_seconds = deadline_seconds
        self.prices = prices
        self.code = code
        self.ranking = RankThenCheck(RankDiseases(hpo), CheckMatch(hpo))
        self.gene_ranking = GeneRank(RankCandidateGenes(hpo))
        self.check = CheckMatch(hpo)
        self.lookup = LookupDisease(hpo)

    def system(self) -> SystemInfo:
        return SystemInfo(
            service_version=version("raredx"),
            code=self.code,
            model_available=self.agent is not None,
            unavailable_because=self.unavailable_because,
            agent=self.agent.params() if self.agent else None,
            agent_with_genes=self.agent_with_genes.params() if self.agent_with_genes else None,
            fallback={
                "without_candidate_genes": self.ranking.name,
                "with_candidate_genes": self.gene_ranking.name,
                **self.ranking.params(),
            },
            limits={
                "max_terms": MAX_TERMS,
                "max_candidate_genes": MAX_GENES,
                "deadline_seconds": self.deadline_seconds,
            },
        )

    def findings(self, request: DiagnoseRequest) -> list[Finding]:
        """The request's terms as they stand in the loaded release: obsolete ids
        replaced, repeats dropped. Raises when a term is unknown — a mistyped finding
        must not be dropped in silence — or when none of them is a finding."""
        unknown: list[str] = []
        found: dict[str, Finding] = {}
        for given in request.hpo_ids:
            try:
                term, label, _ = self.hpo.term(given)
            except RuntimeError:  # hpo3: unknown term
                unknown.append(given)
                continue
            found.setdefault(
                term, Finding(hpo_id=term, label=label, given_as=given if given != term else None)
            )
        if unknown:
            raise UnknownTerms(unknown, self.hpo.release)
        patient, _ = self.hpo.patient(list(found))
        if not len(patient):
            raise NoFinding("none of the terms is a phenotypic finding")
        return list(found.values())

    def diagnose(
        self,
        request: DiagnoseRequest,
        *,
        request_id: str,
        on_step: Callable[[Step], None] | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> DiagnoseResponse:
        """Answer one request. `on_step` is called with each step as it happens; when
        `cancelled()` turns true the agent stops before its next model call."""
        findings = self.findings(request)
        genes = sorted(set(request.candidate_genes or []))  # as evaluated: order says nothing
        question = Question(
            case_id=request_id,
            hpo_ids=[f.hpo_id for f in findings],
            hpo_labels=[f.label for f in findings],
            sex=SEX[request.sex],
            candidate_genes=genes or None,
        )
        started = time.monotonic()
        steps = _Steps(started, on_step)
        watcher = Watcher(steps.event, started + self.deadline_seconds, cancelled)
        outcome: dict[str, Any] = {}

        # The root span of the request's trace, shaped as the evaluation's: the question
        # in, the candidates out. Everything called inside is a child span.
        @mlflow.trace(name="diagnose", span_type=SpanType.AGENT)
        def answer(question: dict[str, Any]) -> dict[str, Any]:
            q = Question.model_validate(question)
            outcome["trace_id"] = mlflow.get_active_trace_id()
            candidates, mode, reason = self._candidates(q, steps, watcher)
            with mlflow.start_span(name="evidence", span_type=SpanType.CHAIN):
                outcome["diagnoses"] = [
                    self._diagnosis(rank, c, q.hpo_ids)
                    for rank, c in enumerate((c for c in candidates if c.disease_id), 1)
                ]
            outcome["mode"], outcome["reason"] = mode, reason
            mlflow.update_current_trace(
                client_request_id=request_id, tags={"mode": mode, "fallback_reason": reason or ""}
            )
            return {"candidates": [c.model_dump() for c in candidates], "mode": mode}

        with masking.masked(request.exclude_sources):
            answer(question.model_dump())

        uncached = watcher.input_tokens - watcher.cached_input_tokens
        price_in, price_cached, price_out = self.prices
        cost = (
            uncached * price_in
            + watcher.cached_input_tokens * price_cached
            + watcher.output_tokens * price_out
        ) / 1e6
        return DiagnoseResponse(
            request_id=request_id,
            mode=outcome["mode"],
            fallback_reason=outcome["reason"],
            findings=findings,
            diagnoses=outcome["diagnoses"],
            steps=steps.steps,
            usage=Usage(
                seconds=round(time.monotonic() - started, 2),
                model_calls=watcher.model_calls,
                input_tokens=watcher.input_tokens,
                cached_input_tokens=watcher.cached_input_tokens,
                output_tokens=watcher.output_tokens,
                cost_usd_estimate=round(cost, 6),
            ),
            trace_id=outcome["trace_id"],
            system=self.system(),
        )

    def _candidates(
        self, question: Question, steps: _Steps, watcher: Watcher
    ) -> tuple[list[Candidate], Mode, str | None]:
        """The ranked candidates, and whether the agent or the fallback produced them."""
        with mlflow.start_span(name="no-model ranking", span_type=SpanType.CHAIN):
            ordered = self.ranking.ordered(question)
            fallback = [candidate(match) for match, _ in ordered[:10]]
            leading = "; ".join(
                f"{m.disease_name} ({len(r.explained)}/{r.n_findings} findings)"
                for m, r in ordered[:LEADING]
            )
            steps.add(
                "tools",
                f"Phenotype tools: {len(self.hpo.disease_ids):,} diseases ranked, "
                f"the best {len(ordered)} checked against the patient",
                f"Leading: {leading}" if ordered else "No disease shares a finding",
            )
            if question.candidate_genes:
                by_gene = self.gene_ranking.predict(question)
                leading = "; ".join(f"{c.gene} → {c.disease_name}" for c in by_gene[:LEADING])
                steps.add(
                    "tools",
                    f"Gene tool: {len(question.candidate_genes)} candidate genes ranked "
                    "by phenotype",
                    f"Leading: {leading}" if by_gene else "None of them has a known disease",
                )
                fallback = by_gene or fallback

        agent = self.agent_with_genes if question.candidate_genes else self.agent
        reason = self.unavailable_because
        if agent is not None:
            try:
                with watching(watcher):
                    candidates = agent.predict(question)
            except DeadlineExceeded:
                reason = f"no answer within the deadline of {self.deadline_seconds:.0f} s"
            except Cancelled:
                reason = "the caller went away"
            except NoFinalAnswer:
                reason = "the agent gave no final answer"
            except openai.APIError as e:  # connection, timeout, rate limit, 401, 402, 5xx
                status = getattr(e, "status_code", None)
                reason = (
                    f"the model API failed ({type(e).__name__}{f' {status}' if status else ''})"
                )
            else:
                filled = sum(c.reason == FILLED for c in candidates)
                fused = sum(c.reason == FUSED for c in candidates)
                notes = []
                if filled:
                    notes.append(f"{filled} filled in from the tools' order")
                if question.candidate_genes:
                    notes.append(
                        "fused with the candidate-gene ranking"
                        + (f" ({fused} from it alone)" if fused else "")
                    )
                steps.add(
                    "answer",
                    f"Answer: {len(candidates)} diagnoses, first: "
                    f"{candidates[0].disease_name if candidates else 'none'}",
                    "; ".join(notes) or None,
                )
                return candidates, "agent", None
        steps.add(
            "fallback",
            f"Model not used: {reason}",
            "The answer is the tools' ranking above, without a model",
        )
        return fallback, "fallback", reason

    def _diagnosis(self, rank: int, c: Candidate, hpo_ids: list[str]) -> Diagnosis:
        assert c.disease_id is not None
        evidence: Evidence | None = None
        try:
            report = self.check(hpo_ids, c.disease_id)
            profile = self.lookup(c.disease_id, max_features=1)
        except (UnknownDisease, ValidationError):  # the agent may name a disease HPO lacks
            pass
        else:
            evidence = Evidence(
                match=report,
                inheritance=profile.inheritance,
                onset_and_course=profile.onset_and_course,
                genes=profile.genes,
                sources=profile.sources,
            )
        return Diagnosis(
            rank=rank,
            disease_id=c.disease_id,
            disease_name=evidence.match.disease_name if evidence else c.disease_name,
            gene=c.gene,
            reason=c.reason,
            evidence=evidence,
        )

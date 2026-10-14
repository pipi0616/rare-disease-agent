"""The evaluation harness, built on MLflow's native GenAI evaluation.

    dataset   each frozen manifest is registered as an MLflow evaluation dataset named
              after it and tagged with its sha256: inputs hold the question, expectations
              the confirmed diagnosis. The manifest in git stays the definition.
    evaluate  mlflow.genai.evaluate asks the system about every record, in parallel.
              Each answer is a trace; a failure is an ERROR trace and scores as a miss.
    mask      while the system works on a case, the case's source paper is hidden from
              the knowledge its tools read, so no tool reads the answer.
    api       a case that failed because the model API failed (no credit, rate limit,
              server error, timeout) says nothing about the system: such failures are
              counted apart and the run is tagged model_api_errors, to be rerun.
    audit     after the run, every tool output in the traces is read back: none may
              show the case's own paper, or a disease known only from it. The counts
              are logged, and the run is tagged leak_audit=passed or failed — or "no
              tool outputs" for a system that reads none, which is not a pass.
    scorer    a code check (@scorer) applying the rules in scoring.py: top-k hits for
              disease and gene, gene checks only where the case has a causal gene.
    run       one MLflow run per evaluation in the experiment eval/<manifest>: params say
              what ran, metrics hold MLflow's means plus our Wilson bounds, and the traces
              keep every question and answer.

Re-scoring evaluates a run's recorded traces again with the current scorer. The
system is not asked again — for a model, nothing is paid again.
"""

import json
import re
import statistics
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import mlflow
from mlflow import MlflowClient
from mlflow.entities import Feedback, SpanType
from mlflow.genai import datasets
from mlflow.genai.datasets import EvaluationDataset
from mlflow.genai.scorers import scorer

from raredx.data.cases import Case
from raredx.evals import scoring
from raredx.evals.scoring import KS
from raredx.evals.systems import Candidate, Question, System
from raredx.knowledge import masking

HEADLINE = ("disease_top1", "disease_top10", "gene_top10")

# Exceptions that mean the model API could not be used — it failed, or the run's spending
# cap stopped the call — not that the system under test got the case wrong.
MODEL_API_ERRORS = frozenset(
    {
        "APIConnectionError",
        "APIStatusError",
        "APITimeoutError",
        "AuthenticationError",
        "InternalServerError",
        "PermissionDeniedError",
        "RateLimitError",
        "BudgetExceeded",  # ours: the run's spending cap stopped the call
        "DeepRareAPIError",  # DeepRare gave no answer after one of its API calls failed
    }
)


class ManifestMismatch(Exception):
    pass


class IncompleteRun(Exception):
    """Fewer answers were recorded than cases asked: the run is not scored."""


def experiment_name(manifest: str) -> str:
    return f"eval/{manifest}"


# ── data ────────────────────────────────────────────────────────────


def record_of(case: Case, candidate_genes: list[str] | None = None) -> dict[str, Any]:
    """One evaluation record: what the system sees, and what the scorer checks against."""
    question = Question(
        case_id=case.id,
        hpo_ids=case.hpo_ids,
        hpo_labels=case.hpo_labels,
        sex=case.sex,
        candidate_genes=candidate_genes,
    )
    expectations: dict[str, str] = {
        "disease_id": case.disease_id,
        "disease_label": case.disease_label,
    }
    if case.gene:  # MLflow expectations cannot be empty; gene-less cases simply have none
        expectations["gene"] = case.gene
    return {"inputs": {"question": question.model_dump()}, "expectations": expectations}


# ── the scorer ──────────────────────────────────────────────────────


def candidates_of(outputs: Any) -> list[Candidate]:
    """The ranked answer inside a system's output; nothing if the system failed."""
    if not isinstance(outputs, dict):
        return []
    return [Candidate.model_validate(c) for c in outputs.get("candidates", [])]


@scorer
def diagnosis(outputs: Any, expectations: dict[str, Any]) -> list[Feedback]:
    """Code check: is the confirmed disease (and gene) among the top k candidates?"""
    candidates = candidates_of(outputs)
    disease_rank, gene_rank = scoring.ranks(
        candidates, expectations["disease_id"], expectations.get("gene")
    )
    feedback = [Feedback(name="answered", value=bool(candidates))]
    feedback += [Feedback(name=f"disease_top{k}", value=scoring.found(disease_rank, k)) for k in KS]
    if expectations.get("gene"):
        feedback += [Feedback(name=f"gene_top{k}", value=scoring.found(gene_rank, k)) for k in KS]
    return feedback


def summary_of(metrics: dict[str, float], n_cases: int, n_gene: int) -> scoring.Summary:
    """Our Summary — counts and Wilson intervals — from evaluate()'s per-check means.

    The means come from the scorer's results in memory; the counts follow from the
    number of cases asked, so nothing depends on reading records back.
    """

    def count(name: str, n: int) -> int:
        return round(metrics.get(f"{name}/mean", 0.0) * n)

    return scoring.summary_from_counts(
        {k: count(f"disease_top{k}", n_cases) for k in KS},
        n_cases,
        {k: count(f"gene_top{k}", n_gene) for k in KS},
        n_gene,
        count("answered", n_cases),
    )


def wilson_metrics(summary: scoring.Summary) -> dict[str, float]:
    values: dict[str, float] = {"n_cases": summary.n_cases, "n_answered": summary.n_answered}
    for target, rates in (("disease", summary.disease), ("gene", summary.gene)):
        for k in KS:
            values[f"{target}_top{k}/low"] = rates[k].low
            values[f"{target}_top{k}/high"] = rates[k].high
    return values


# ── the harness ─────────────────────────────────────────────────────


class Harness:
    def __init__(self, tracking_uri: str, artifact_root: Path) -> None:
        self.tracking_uri = tracking_uri
        self.artifact_root = artifact_root
        self.client = MlflowClient(tracking_uri=tracking_uri)

    def _use(self, manifest: str) -> str:
        """Point MLflow at this store and the manifest's experiment; returns its id."""
        mlflow.set_tracking_uri(self.tracking_uri)
        name = experiment_name(manifest)
        found = self.client.get_experiment_by_name(name)
        if found is None:
            location = (self.artifact_root / name.replace("/", "-")).resolve().as_uri()
            experiment_id = str(self.client.create_experiment(name, artifact_location=location))
        else:
            experiment_id = str(found.experiment_id)
        mlflow.set_experiment(experiment_id=experiment_id)
        return experiment_id

    def dataset(
        self,
        manifest: str,
        manifest_sha256: str,
        cases: list[Case],
        genes: dict[str, list[str]] | None = None,
    ) -> EvaluationDataset:
        """The manifest as an MLflow evaluation dataset, registered once and reused. With
        candidate genes it is the genotype track's: a name and a hash of its own."""
        experiment_id = self._use(manifest)
        for existing in datasets.search_datasets(experiment_ids=[experiment_id]):
            if existing.name == manifest:
                if (existing.tags or {}).get("manifest_sha256") != manifest_sha256:
                    raise ManifestMismatch(
                        f"dataset {manifest} was registered from a different manifest"
                    )
                return existing
        dataset = datasets.create_dataset(
            name=manifest, experiment_id=[experiment_id], tags={"manifest_sha256": manifest_sha256}
        )
        dataset.merge_records([record_of(c, (genes or {}).get(c.id)) for c in cases])
        return dataset  # type: ignore[no-any-return]  # create_dataset is untyped

    def evaluate(
        self,
        system: System,
        manifest: str,
        manifest_sha256: str,
        cases: list[Case],
        params: dict[str, Any],
        *,
        mask_source_papers: bool = True,
        hidden_of: Callable[[str], set[str]] | None = None,
        genes: dict[str, list[str]] | None = None,
        part: bool = False,
    ) -> tuple[str, scoring.Summary]:
        """Run the system on the manifest and record it; returns the MLflow run id and Summary.

        `part`: the cases are a part of the manifest — those a run lost to the model API,
        asked again — so they are evaluated as they are, not as the registered dataset.

        While the system works on a case, the case's source paper is masked from the
        knowledge its tools read (raredx.knowledge.masking). Turning that off measures
        how much a score owed to reading the answer; such runs are named "(unmasked)".

        A masked run is then audited (leak_audit). `hidden_of` gives, for a paper, the
        diseases known only from it; without it only the paper itself is looked for.
        """
        if part:
            self._use(manifest)
            data: Any = [record_of(c, (genes or {}).get(c.id)) for c in cases]
        else:
            data = self.dataset(manifest, manifest_sha256, cases, genes)
        papers = {c.id: c.pmid for c in cases}

        # The root span of every trace: one per question. Anything the system calls
        # inside — a model, a tool — appears as a child span.
        @mlflow.trace(name=system.name, span_type=SpanType.CHAIN)
        def predict(question: dict[str, Any]) -> dict[str, Any]:
            q = Question.model_validate(question)
            with masking.masked([papers[q.case_id]] if mask_source_papers else []):
                answer = system.predict(q)
            return {"candidates": [c.model_dump() for c in answer]}

        run_name = system.name if mask_source_papers else f"{system.name} (unmasked)"
        mask = "case source paper" if mask_source_papers else "none"
        with mlflow.start_run(run_name=run_name) as run:
            mlflow.log_params({**params, "knowledge_mask": mask})
            started = time.monotonic()
            result = mlflow.genai.evaluate(data=data, predict_fn=predict, scorers=[diagnosis])
            mlflow.log_metric("usage/wall_seconds", round(time.monotonic() - started, 1))
            self._check_complete(run.info.run_id, expected=len(cases))
            api_errors, first = self.model_api_errors(run.info.run_id)
            mlflow.log_metric("errors/model_api", api_errors)
            if api_errors:
                mlflow.set_tag("model_api_errors", first)
            if mask_source_papers:
                audit = self.leak_audit(run.info.run_id, papers, hidden_of)
                mlflow.log_metrics(audit)
                leaked = audit["leak/own_paper_shown"] + audit["leak/hidden_disease_shown"]
                verdict = "failed" if leaked else "passed"
                if not audit["leak/tool_outputs_read"]:
                    verdict = "no tool outputs"  # nothing to read: not a pass
                mlflow.set_tag("leak_audit", verdict)
            n_gene = sum(c.gene is not None for c in cases)
            summary = summary_of(result.metrics, len(cases), n_gene)
            mlflow.log_metrics(wilson_metrics(summary))
        return str(run.info.run_id), summary

    def traces(self, run_id: str) -> list[Any]:
        """The traces a run recorded, once pending writes are flushed."""
        mlflow.flush_trace_async_logging()
        experiment_id = self.client.get_run(run_id).info.experiment_id
        traces = mlflow.search_traces(
            locations=[experiment_id], run_id=run_id, return_type="list", max_results=100_000
        )
        return list(traces)

    def answers(self, run_id: str) -> list[Any]:
        """One trace per case: the one that answered it.

        MLflow's evaluate asks a case again when the model API says it is busy (HTTP
        429), and records every attempt as a trace of its own. The case's answer is its
        last attempt; the earlier ones are what the rate limit cost in time."""
        last: dict[str, Any] = {}
        for trace in sorted(self.traces(run_id), key=lambda t: t.info.request_time):
            last[trace.data.spans[0].inputs["question"]["case_id"]] = trace
        return list(last.values())

    def _check_complete(self, run_id: str, expected: int) -> None:
        """Refuse to score a run whose answers did not all reach MLflow."""
        recorded = len(self.answers(run_id))
        if recorded != expected:
            raise IncompleteRun(
                f"only {recorded} of {expected} answers were recorded in MLflow; "
                "the run is marked failed and was not scored — run it again"
            )

    def lost_cases(self, run_id: str) -> dict[str, str]:
        """The cases a run lost because the model API failed, each with its error. A case
        asked again after a rate limit, and answered, was not lost."""
        lost = {}
        for trace in self.answers(run_id):
            errors = [
                e.attributes
                for span in trace.data.spans
                for e in span.events
                if e.name == "exception" and e.attributes.get("exception.type") in MODEL_API_ERRORS
            ]
            if errors:
                case_id = trace.data.spans[0].inputs["question"]["case_id"]
                lost[case_id] = str(errors[0].get("exception.message", ""))[:300]
        return lost

    def model_api_errors(self, run_id: str) -> tuple[int, str]:
        """How many cases failed because the model API failed, and the first such error."""
        lost = self.lost_cases(run_id)
        return len(lost), next(iter(lost.values()), "")

    def leak_audit(
        self,
        run_id: str,
        papers: dict[str, str],
        hidden_of: Callable[[str], set[str]] | None = None,
    ) -> dict[str, float]:
        """Read back every tool output the run recorded and count those that show the
        case's own paper, or a disease known only from it. Both counts must be 0."""
        outputs = own = hidden = 0
        for trace in self.traces(run_id):
            pmid = papers[trace.data.spans[0].inputs["question"]["case_id"]]
            paper = re.compile(re.escape(pmid) + r"(?!\d)")
            diseases = sorted(hidden_of(pmid)) if hidden_of else []
            disease = re.compile("|".join(re.escape(d) + r"(?!\d)" for d in diseases))
            for span in trace.data.spans:
                if span.span_type != SpanType.TOOL:
                    continue
                text = json.dumps(span.outputs, default=str)
                outputs += 1
                own += bool(paper.search(text))
                hidden += bool(diseases and disease.search(text))
        return {
            "leak/tool_outputs_read": outputs,
            "leak/own_paper_shown": own,
            "leak/hidden_disease_shown": hidden,
        }

    def hits(self, run_id: str, k: int) -> dict[str, bool]:
        """Per case: whether the run had the confirmed disease in its top k — the
        scorer's verdict as recorded on each trace."""
        verdicts = {}
        for trace in self.answers(run_id):
            case_id = trace.data.spans[0].inputs["question"]["case_id"]
            found = [a.value for a in trace.info.assessments if a.name == f"disease_top{k}"]
            verdicts[case_id] = bool(found[-1]) if found else False
        return verdicts

    def usage(self, run_id: str) -> dict[str, float]:
        """Tokens and time a run used, summed from its traces' model calls."""
        traces = self.traces(run_id)
        tokens = [t.info.token_usage or {} for t in traces]
        durations = [t.info.execution_duration for t in traces if t.info.execution_duration]
        return {
            "usage/input_tokens": sum(u.get("input_tokens", 0) for u in tokens),
            "usage/cached_input_tokens": sum(u.get("cache_read_input_tokens", 0) for u in tokens),
            "usage/output_tokens": sum(u.get("output_tokens", 0) for u in tokens),
            "usage/seconds_per_case": statistics.median(durations) / 1000 if durations else 0.0,
        }

    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        now = int(time.time() * 1000)
        for key, value in metrics.items():
            self.client.log_metric(run_id, key, value, timestamp=now)

    def rescore(
        self, run_id: str, manifest_sha256: str, expected: int
    ) -> tuple[str, scoring.Summary, dict[str, str]]:
        """Score a run's recorded answers again, as a new run. The system is not asked again."""
        params = dict(self.client.get_run(run_id).data.params)
        if params.get("manifest_sha256") != manifest_sha256:
            raise ManifestMismatch(
                f"the manifest changed since run {run_id}; scores would not compare"
            )
        self._use(params.get("label", params["manifest"]))
        traces = self.answers(run_id)
        if len(traces) != expected:
            raise IncompleteRun(f"run {run_id} recorded {len(traces)} of {expected} answers")
        n_gene = sum(any(a.name == "gene" for a in t.info.assessments) for t in traces)
        with mlflow.start_run(run_name=f"{params['system']} (rescored)") as run:
            mlflow.log_params({**params, "rescored_from": run_id})
            result = mlflow.genai.evaluate(data=traces, scorers=[diagnosis])
            summary = summary_of(result.metrics, len(traces), n_gene)
            mlflow.log_metrics(wilson_metrics(summary))
        return str(run.info.run_id), summary, params

    def runs(self, manifest: str) -> list[dict[str, Any]]:
        """Every run on a manifest, newest first, with its headline numbers."""
        found = self.client.get_experiment_by_name(experiment_name(manifest))
        if found is None:
            return []
        rows = []
        for run in self.client.search_runs(
            [found.experiment_id], order_by=["attributes.start_time DESC"]
        ):
            row = {
                "run_id": run.info.run_id,
                "name": run.info.run_name,
                "start_time": run.info.start_time,
            }
            row["code"] = run.data.params.get("code", "")
            row.update({k: run.data.metrics.get(f"{k}/mean") for k in HEADLINE})
            rows.append(row)
        return rows

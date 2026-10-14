"""A reader measured against hand-annotated text: the terms of each document, as sets.

Per document, the terms the reader gives are compared with the terms the annotators
gave — the document-level measure of PhenoTagger, PhenoBERT and AutoPCR. Both sides
are taken under "Phenotypic abnormality" in our HPO release:

- an annotation made against an older release is brought up to date (an alternative
  id, an obsolete term's replacement); one that is no finding in our release, or that
  it no longer has, is set aside — nobody could find it — and counted;
- a term the reader gives that the release does not know at all counts as wrong.

The headline is micro-averaged (the documents' counts pooled), as AutoPCR reports;
macro (each document's own scores averaged), as PhenoBERT reports, stands beside it.
Every mention counts whatever the note says of it, as in those papers; how the reader
handled what a note denies is reported apart, and so is "present only" — the terms a
diagnosis is asked about.

A run is mlflow.genai.evaluate over the documents, in experiment eval/notes-<corpus>:
each document's reading is a trace, and a code scorer counts its agreements. Each
reading is also saved to a file as it arrives and read back on a rerun, so a run
stopped by the model API resumes where it stopped and pays nothing twice.
"""

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

import mlflow
from mlflow import MlflowClient
from mlflow.entities import Feedback, SpanType
from mlflow.genai.scorers import scorer

from raredx.knowledge.hpo import HPO
from raredx.phenotyping.corpora import Document
from raredx.phenotyping.reader import Finding, Reader

EXPERIMENT = "eval/notes-{corpus}"


def gold_terms(document: Document, hpo: HPO) -> tuple[set[str], set[str], int]:
    """The annotators' terms in this release — all of them, and those the text denies —
    and how many annotated terms were set aside."""
    found, negated, aside = set(), set(), set()
    for a in document.gold:
        current = hpo.current(a.hpo_id)
        if current is None or not hpo.is_finding(current):
            aside.add(a.hpo_id)
            continue
        found.add(current)
        if a.kind == "negated":
            negated.add(current)
    # A term both stated and denied in one note is stated: it is not counted as denied.
    stated = {hpo.current(a.hpo_id) for a in document.gold if a.kind != "negated"}
    return found, negated - stated, len(aside)


def reader_terms(findings: list[Finding], hpo: HPO, status: str | None = None) -> set[str]:
    """The reader's terms in this release (with this status, if given). An id the
    release does not know stays as given: it counts as wrong."""
    out = set()
    for f in findings:
        if f.hpo_id is None or (status is not None and f.status != status):
            continue
        current = hpo.current(f.hpo_id)
        if current is None:
            out.add(f.hpo_id)
        elif hpo.is_finding(current):
            out.add(current)
    return out


def scores(gold: set[str], found: set[str]) -> tuple[float, float, float]:
    """One document's precision, recall and F1 — PhenoBERT's conventions: both sets
    empty is perfect; one of them empty is zero."""
    if not gold and not found:
        return 1.0, 1.0, 1.0
    if not gold or not found:
        return 0.0, 0.0, 0.0
    hit = len(gold & found)
    p, r = hit / len(found), hit / len(gold)
    return p, r, (2 * p * r / (p + r) if hit else 0.0)


@scorer
def agreement(outputs: Any, expectations: dict[str, Any]) -> list[Feedback]:
    """Code check: the document's terms against the annotators'."""
    answered = isinstance(outputs, dict)
    found = set(outputs["terms"]) if answered else set()
    present = set(outputs["present"]) if answered else set()
    absent = set(outputs["absent"]) if answered else set()
    gold, negated = set(expectations["terms"]), set(expectations.get("negated", []))
    p, r, f1 = scores(gold, found)
    stated = gold - negated
    values: dict[str, float] = {
        "answered": answered,
        "tp": len(gold & found),
        "fp": len(found - gold),
        "fn": len(gold - found),
        "precision": p,
        "recall": r,
        "f1": f1,
        "present_tp": len(stated & present),
        "present_fp": len(present - stated),
        "present_fn": len(stated - present),
        "negated": len(negated),
        "negated_as_absent": len(negated & absent),
        "negated_as_present": len(negated & present),
    }
    return [Feedback(name=k, value=v) for k, v in values.items()]


def summarize(means: dict[str, float], n: int) -> dict[str, float]:
    """Micro and macro scores from evaluate()'s per-document means."""

    def total(name: str) -> float:
        return round(means.get(f"{name}/mean", 0.0) * n)

    def micro(tp: float, fp: float, fn: float) -> tuple[float, float, float]:
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        return p, r, (2 * p * r / (p + r) if p + r else 0.0)

    p, r, f1 = micro(total("tp"), total("fp"), total("fn"))
    pp, pr, pf1 = micro(total("present_tp"), total("present_fp"), total("present_fn"))
    return {
        "n_documents": n,
        "n_answered": total("answered"),
        "micro/precision": p,
        "micro/recall": r,
        "micro/f1": f1,
        "macro/precision": means.get("precision/mean", 0.0),
        "macro/recall": means.get("recall/mean", 0.0),
        "macro/f1": means.get("f1/mean", 0.0),
        "present/precision": pp,
        "present/recall": pr,
        "present/f1": pf1,
        "negated/n": total("negated"),
        "negated/as_absent": total("negated_as_absent"),
        "negated/as_present": total("negated_as_present"),
    }


def _experiment(tracking_uri: str, artifact_root: Path, corpus: str) -> None:
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient(tracking_uri=tracking_uri)
    name = EXPERIMENT.format(corpus=corpus)
    found = client.get_experiment_by_name(name)
    if found is None:
        location = (artifact_root / name.replace("/", "-")).resolve().as_uri()
        experiment_id = str(client.create_experiment(name, artifact_location=location))
    else:
        experiment_id = str(found.experiment_id)
    mlflow.set_experiment(experiment_id=experiment_id)


def saved_dir(answers: Path, reader: Reader) -> Path:
    """Where this reader's readings are saved: one folder per configuration."""
    key = json.dumps(reader.config(), sort_keys=True)
    return answers / f"{reader.name}-{hashlib.sha256(key.encode()).hexdigest()[:12]}"


def evaluate(
    reader: Reader,
    documents: list[Document],
    corpus: str,
    hpo: HPO,
    *,
    tracking_uri: str,
    artifact_root: Path,
    answers: Path | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[str, dict[str, float]]:
    """Read every document and score it; returns the MLflow run id and the scores."""
    _experiment(tracking_uri, artifact_root, corpus)
    data, aside = [], 0
    for d in documents:
        gold, negated, set_aside = gold_terms(d, hpo)
        aside += set_aside
        data.append(
            {
                "inputs": {"document": {"id": d.id, "text": d.text}},
                "expectations": {"terms": sorted(gold), "negated": sorted(negated)},
            }
        )
    folder = saved_dir(answers, reader) if answers is not None else None
    read_back = 0
    lock = threading.Lock()

    def findings_of(document: dict[str, str]) -> list[Finding]:
        nonlocal read_back
        saved = folder / f"{corpus}-{document['id']}.json" if folder is not None else None
        if saved is not None and saved.exists():
            with lock:
                read_back += 1
            return [Finding.model_validate(f) for f in json.loads(saved.read_text())]
        findings = reader.read(document["text"])
        if saved is not None:
            saved.parent.mkdir(parents=True, exist_ok=True)
            part = saved.with_suffix(".part")
            part.write_text(json.dumps([f.model_dump() for f in findings], ensure_ascii=False))
            part.replace(saved)
        return findings

    @mlflow.trace(name=reader.name, span_type=SpanType.CHAIN)
    def predict(document: dict[str, str]) -> dict[str, Any]:
        findings = findings_of(document)
        return {
            "findings": [f.model_dump() for f in findings],
            "terms": sorted(reader_terms(findings, hpo)),
            "present": sorted(reader_terms(findings, hpo, "present")),
            "absent": sorted(reader_terms(findings, hpo, "absent")),
        }

    with mlflow.start_run(run_name=f"{reader.name} · {corpus}") as run:
        mlflow.log_params(
            {**reader.config(), **(params or {}), "corpus": corpus, "n_documents": len(documents)}
        )
        started = time.monotonic()
        result = mlflow.genai.evaluate(data=data, predict_fn=predict, scorers=[agreement])
        metrics = summarize(result.metrics, len(documents))
        metrics["gold/set_aside"] = aside
        metrics["usage/read_back"] = read_back
        metrics["usage/wall_seconds"] = round(time.monotonic() - started, 1)
        mlflow.log_metrics(metrics)
    return str(run.info.run_id), metrics

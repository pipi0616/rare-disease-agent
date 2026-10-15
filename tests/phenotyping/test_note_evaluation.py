"""Scoring a reader: terms per document, as sets, against the annotators'."""

from pathlib import Path

import mlflow
import pytest

from raredx.knowledge.hpo import HPO
from raredx.phenotyping.corpora import Annotation, Document
from raredx.phenotyping.evaluation import (
    evaluate,
    gold_terms,
    paired,
    per_document,
    reader_terms,
    scores,
    summarize,
)
from raredx.phenotyping.reader import DictionaryReader, Finding


def note(doc_id: str, text: str, *gold: tuple[str, str]) -> Document:
    return Document(
        id=doc_id,
        text=text,
        gold=[Annotation(start=0, end=1, text="x", hpo_id=i, kind=k) for i, k in gold],  # type: ignore[arg-type]
    )


def test_the_annotations_are_brought_up_to_this_release(hpo: HPO) -> None:
    doc = note(
        "n",
        "",
        ("HP:0001730", "plain"),  # an alternative id of Hearing impairment
        ("HP:0099999", "plain"),  # obsolete: Sensorineural hearing impairment now
        ("HP:0000007", "plain"),  # an inheritance: no finding, set aside
        ("HP:0000000", "plain"),  # unknown to this release: set aside
        ("HP:0001250", "negated"),
        ("HP:0000510", "negated"),
        ("HP:0000510", "plain"),  # denied once, stated once: stated
    )
    found, negated, aside = gold_terms(doc, hpo)
    assert found == {"HP:0000365", "HP:0000407", "HP:0001250", "HP:0000510"}
    assert negated == {"HP:0001250"}
    assert aside == 2


def test_a_reader_term_unknown_to_the_release_counts_against_it(hpo: HPO) -> None:
    findings = [
        Finding(quote="a", finding="", hpo_id="HP:9999999"),  # invented: kept, so wrong
        Finding(quote="b", finding="", hpo_id="HP:0000007"),  # no finding: left out
        Finding(quote="c", finding="", hpo_id="HP:0001730", status="absent"),
    ]
    assert reader_terms(findings, hpo) == {"HP:9999999", "HP:0000365"}
    assert reader_terms(findings, hpo, "present") == {"HP:9999999"}


@pytest.mark.parametrize(
    ("gold", "found", "expected"),
    [
        (set(), set(), (1.0, 1.0, 1.0)),  # nothing to find, nothing found: perfect
        ({"a"}, set(), (0.0, 0.0, 0.0)),
        (set(), {"a"}, (0.0, 0.0, 0.0)),
        ({"a", "b"}, {"a", "c", "d", "e"}, (0.25, 0.5, 1 / 3)),
    ],
)
def test_one_documents_scores_follow_phenoberts_conventions(
    gold: set[str], found: set[str], expected: tuple[float, float, float]
) -> None:
    assert scores(gold, found) == pytest.approx(expected)


def test_micro_pools_the_counts_and_macro_averages_the_documents() -> None:
    # Two documents: 3 right, 1 wrong, 0 missed; and 0 right, 0 wrong, 4 missed.
    means = {"tp/mean": 1.5, "fp/mean": 0.5, "fn/mean": 2.0, "answered/mean": 1.0}
    means |= {"precision/mean": 0.375, "recall/mean": 0.5, "f1/mean": 0.43}
    summary = summarize(means, 2)
    assert summary["micro/precision"] == 0.75 and summary["micro/recall"] == 3 / 7
    assert summary["macro/precision"] == 0.375 and summary["n_answered"] == 2


def test_a_run_scores_every_document_and_reads_saved_readings_back(
    hpo: HPO, tmp_path: Path
) -> None:
    docs = [
        note("a", "Seizures and hearing loss.", ("HP:0001250", "plain"), ("HP:0000510", "plain")),
        note("b", "Nothing of note.", ("HP:0000786", "plain")),
    ]
    store = f"sqlite:///{tmp_path / 'mlflow.db'}"
    answers = tmp_path / "answers"
    run_id, metrics = evaluate(
        DictionaryReader(hpo), docs, "tiny", hpo,
        tracking_uri=store, artifact_root=tmp_path / "mlruns", answers=answers,
    )  # fmt: skip
    # a: Seizure right, Hearing impairment wrong, Rod-cone dystrophy missed; b: missed
    assert (metrics["micro/precision"], metrics["micro/recall"]) == (0.5, 1 / 3)
    assert metrics["n_answered"] == 2 and metrics["usage/read_back"] == 0
    assert len(list(answers.rglob("tiny-*.json"))) == 2
    again = evaluate(
        DictionaryReader(hpo), docs, "tiny", hpo,
        tracking_uri=store, artifact_root=tmp_path / "mlruns", answers=answers,
    )[1]  # fmt: skip
    assert again["usage/read_back"] == 2 and again["micro/f1"] == metrics["micro/f1"]
    run = mlflow.MlflowClient(store).get_run(run_id)
    assert run.data.params["reader"] == "dictionary"
    scored = per_document(store, run_id)
    assert scored["a"] == {"precision": 0.5, "recall": 0.5, "f1": 0.5}
    assert scored["b"]["f1"] == 0.0
    assert mlflow.get_experiment(run.info.experiment_id).name == "eval/notes-tiny"


def test_two_readers_are_compared_document_by_document() -> None:
    a = {"1": {"f1": 0.9}, "2": {"f1": 0.5}, "3": {"f1": 0.7}, "4": {"f1": 0.2}}
    b = {"1": {"f1": 0.6}, "2": {"f1": 0.5}, "3": {"f1": 0.4}, "5": {"f1": 1.0}}
    wins, losses, p = paired(a, b)
    assert (wins, losses) == (2, 0)  # a tie (2) and documents only one read do not count
    assert p == 0.5

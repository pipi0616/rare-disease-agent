"""RareArena's case reports: reading the file, mapping PMC ids, and the sample's rules."""

import csv
from collections import Counter
from pathlib import Path

import httpx
import pytest

from raredx.data import rarearena
from raredx.data.rarearena import Report

COLUMNS = [
    "_id",
    "case_report",
    "diagnosis",
    "Orpha_name",
    "Orpha_id",
    "age",
    "gender",
    "embedding",
]


def test_reports_are_read_without_their_embeddings(tmp_path: Path) -> None:
    path = tmp_path / rarearena.FILE
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerow(
            [
                "123-1",
                "A 3-year-old girl ...",
                "x",
                "Behçet disease",
                "117",
                "[[3.0, 'year']]",
                "F",
                "[0.1, 0.2]",
            ]
        )
        writer.writerow(["456-2", "A man ...", "y", "", "81", "[]", "?", "[0.3]"])
    first, second = rarearena.reports(path)
    assert (first.id, first.pmcid, first.disease_id, first.disease_label, first.sex) == (
        "RareArena_123-1",
        "PMC123",
        "ORPHA:117",
        "Behçet disease",
        "FEMALE",
    )
    assert second.disease_label == "y" and second.sex is None  # the diagnosis when no name


def test_pmc_ids_are_mapped_once_each(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    asked: list[str] = []

    def reply(request: httpx.Request) -> httpx.Response:
        ids = request.url.params["ids"].split(",")
        asked.extend(ids)
        records = [{"pmcid": i, "pmid": int(i[3:]) * 10} for i in ids if i != "PMC9"]
        return httpx.Response(200, json={"records": records})

    client = httpx.Client(transport=httpx.MockTransport(reply))
    convert = rarearena.convert
    monkeypatch.setattr(rarearena, "convert", lambda ids: convert(ids, client))
    path = tmp_path / "pmc_pmids.tsv"
    assert rarearena.update_pmids(path, {"PMC1", "PMC2", "PMC9"}) == 2  # PMC9 has no PMID
    assert rarearena.update_pmids(path, {"PMC1", "PMC3"}) == 1
    assert asked == ["PMC1", "PMC2", "PMC9", "PMC3"]
    assert rarearena.read_pmids(path) == {"PMC1": "PMID:10", "PMC2": "PMID:20", "PMC3": "PMID:30"}


def report(i: int, paper: int, disease: str) -> Report:
    return Report(
        id=f"RareArena_{paper}-{i}",
        pmcid=f"PMC{paper}",
        text="...",
        disease_id=disease,
        disease_label=disease,
        age="",
        sex=None,
    )


def test_the_sample_takes_one_report_per_paper_and_a_few_per_disease() -> None:
    reports = [report(i, paper, f"ORPHA:{paper % 7}") for paper in range(60) for i in (1, 2)]
    pmids = {f"PMC{p}": f"PMID:{p}" for p in range(60)}
    band = {"ORPHA:0": "1 in 100,000 or more", "ORPHA:1": "1 in 100,000 or more"}
    chosen = rarearena.sample(reports, pmids, band, n=12)
    assert len(chosen) == 12
    assert len({r.pmcid for r in chosen}) == 12  # one per paper
    assert max(Counter(r.disease_id for r in chosen).values()) <= rarearena.PER_DISEASE
    common = sum(band.get(r.disease_id) == "1 in 100,000 or more" for r in chosen)
    assert common >= 4  # at least a third
    assert chosen == rarearena.sample(reports, pmids, band, n=12)  # the seed fixes it

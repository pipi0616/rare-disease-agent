"""Publication dates from PubMed: parsed from recorded replies, fetched through a fake transport."""

from datetime import date
from pathlib import Path

import httpx
import pytest

from raredx.data import pubmed

# The parts of an esummary record that are read, as PubMed returns them.
SUMMARY = {
    "pubdate": "2026 Feb",
    "epubdate": "2025 Sep 25",
    "history": [
        {"pubstatus": "received", "date": "2025/03/01 00:00"},  # not public yet
        {"pubstatus": "entrez", "date": "2025/09/26 06:23"},
        {"pubstatus": "pubmed", "date": "2025/09/26 06:23"},
    ],
}


def test_written_dates_are_never_made_later_than_they_were() -> None:
    assert pubmed.parse_written("2025 Nov 18") == date(2025, 11, 18)
    assert pubmed.parse_written("2026 Jan-Feb") == date(2026, 1, 1)
    assert pubmed.parse_written("2019 Winter") == date(2019, 1, 1)
    assert pubmed.parse_written("") is None


def test_the_first_public_day_is_the_earliest_public_date() -> None:
    first, entrez, epub, issue = pubmed.first_public(SUMMARY)
    assert (first, entrez, epub, issue) == (
        date(2025, 9, 25),
        date(2025, 9, 26),
        date(2025, 9, 25),
        date(2026, 2, 1),
    )
    # an old paper in print long before PubMed listed it
    old = {"pubdate": "1991 Mar", "history": [{"pubstatus": "entrez", "date": "2001/01/01 00:00"}]}
    assert pubmed.first_public(old)[0] == date(1991, 3, 1)


def test_update_asks_only_for_papers_not_yet_listed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asked: list[str] = []

    def reply(request: httpx.Request) -> httpx.Response:
        ids = dict(httpx.QueryParams(request.content.decode()))["id"].split(",")
        asked.extend(ids)
        return httpx.Response(200, json={"result": dict.fromkeys(ids, SUMMARY)})

    client = httpx.Client(transport=httpx.MockTransport(reply))
    fetch = pubmed.fetch
    monkeypatch.setattr(pubmed, "fetch", lambda pmids: fetch(pmids, client))
    path = tmp_path / "dates.tsv"
    assert pubmed.update(path, {"PMID:1", "PMID:2"}) == 2
    assert pubmed.update(path, {"PMID:1", "PMID:3"}) == 1
    assert asked == ["1", "2", "3"]
    assert pubmed.read(path) == {f"PMID:{i}": date(2025, 9, 25) for i in (1, 2, 3)}
    assert path.read_text().splitlines()[0] == pubmed.HEADER

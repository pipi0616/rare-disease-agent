"""When a paper first became public, from PubMed (NCBI E-utilities).

The temporal test needs, for each case's paper, the first day anyone could have read
it — a model's training crawl included. PubMed keeps several dates per paper; the
earliest public one is taken: the day the record entered PubMed ("entrez"), the
electronic publication date, or the issue's date, whichever came first (an old paper
can be in print years before PubMed lists it). Dates before publication (received,
accepted, revised) are not public and are not used. A date without its day counts as
the first of its month, without its month ("2019 Winter") as the first of its year:
a paper is never made later than it was.
A preprint can come earlier still; PubMed does not say, and that stays a caveat.

The dates are kept in evals/pubmed_dates.tsv, in git: the temporal manifest is
chosen from them, so they are part of its definition, read again without a network.
"""

import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import httpx

ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBLIC = ("entrez", "pubmed", "aheadofprint", "epublish")  # history statuses anyone could see
BATCH = 200
HEADER = "pmid\tfirst_public\tentrez\tepub\tissue"
MONTHS = {
    m: i
    for i, m in enumerate(
        ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1
    )
}


def parse_written(text: str) -> date | None:
    """PubMed's written dates ("2025 Nov 18", "2025 Nov", "2026") as a date; the first
    of the month (or year) when the day (or month) is missing; None if unreadable."""
    match = re.match(r"(\d{4})(?: ([A-Z][a-z]{2}))?(?: (\d{1,2}))?", text.strip())
    if not match:
        return None
    year, month, day = match.groups()
    return date(int(year), MONTHS.get(month or "", 1), int(day or 1))


def first_public(summary: Mapping[str, object]) -> tuple[date | None, ...]:
    """(first public day, entrez date, electronic publication date, issue date) of one
    PubMed record."""
    history = summary.get("history") or []
    entrez = None
    public = []
    for entry in history if isinstance(history, list) else []:
        status, written = entry.get("pubstatus"), str(entry.get("date", ""))
        found = re.match(r"(\d{4})/(\d{2})/(\d{2})", written)
        if status in PUBLIC and found:
            day = date(*map(int, found.groups()))
            public.append(day)
            if status == "entrez":
                entrez = day
    epub = parse_written(str(summary.get("epubdate") or ""))
    issue = parse_written(str(summary.get("pubdate") or ""))
    public += [d for d in (epub, issue) if d]
    return (min(public) if public else None), entrez, epub, issue


def fetch(
    pmids: list[str], client: httpx.Client | None = None
) -> dict[str, tuple[date | None, ...]]:
    """First public, entrez, epub and issue dates of each paper (PMID:n), in batches."""
    own = client is None
    http = client or httpx.Client(timeout=60)
    found: dict[str, tuple[date | None, ...]] = {}
    try:
        for start in range(0, len(pmids), BATCH):
            numbers = [p.removeprefix("PMID:") for p in pmids[start : start + BATCH]]
            data = {"db": "pubmed", "retmode": "json", "tool": "raredx", "id": ",".join(numbers)}
            response = http.post(ESUMMARY, data=data)
            response.raise_for_status()
            result = response.json()["result"]
            for number in numbers:
                if number in result and "error" not in result[number]:
                    found[f"PMID:{number}"] = first_public(result[number])
    finally:
        if own:
            http.close()
    return found


def read(path: Path) -> dict[str, date]:
    """Each paper's first public day, from the table in git."""
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != HEADER:
        raise ValueError(f"{path}: expected header {HEADER!r}")
    out = {}
    for line in lines[1:]:
        pmid, first, *_ = line.split("\t")
        if first:
            out[pmid] = date.fromisoformat(first)
    return out


def update(path: Path, pmids: set[str]) -> int:
    """Add the papers the table lacks, fetched from PubMed; returns how many were added.
    Papers already listed are not asked again: a published date does not change."""
    rows: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines()[1:]:
            rows[line.split("\t")[0]] = line
    missing = sorted(pmids - set(rows))
    found = fetch(missing)
    for pmid, dates in found.items():
        rows[pmid] = "\t".join([pmid, *(d.isoformat() if d else "" for d in dates)])
    path.write_text(HEADER + "\n" + "".join(rows[p] + "\n" for p in sorted(rows)), encoding="utf-8")
    return len(found)

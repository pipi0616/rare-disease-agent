"""Wikipedia's articles on rare diseases, pinned by revision, for text retrieval.

Which articles: those whose Wikidata item carries an Orphanet (P1550) or OMIM (P492)
id of a disease the knowledge has. Wikidata is queried once; each article's current
revision id is then recorded (evals/wikipedia_revisions.tsv, in git), and the
article is fetched as that revision's HTML. Fetching by revision is what makes the
corpus reproducible: an article edited tomorrow is still read as it was.

The HTML is kept as fetched (data/raw/wikipedia/<date>/pages.jsonl.gz); parsing it
into sections, paragraphs and the PubMed ids each paragraph cites is done by
raredx.knowledge.corpus. Requests go one at a time, as Wikimedia's API etiquette
asks, a second apart, with a User-Agent naming the project; no email is sent. Asked
to slow down (429), a request waits as long as the answer says and tries again.

Licence: CC BY-SA 4.0. The text stays on this machine; what is shown is attributed.
"""

import gzip
import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

SPARQL = "https://query.wikidata.org/sparql"
API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "raredx/0.1 (https://github.com/pipi0616/rare-disease-agent)"
PAGES = "pages.jsonl.gz"
HEADER = "title\tpageid\trevid\twikidata\torpha\tomim"
BATCH = 50  # titles per revision query, the API's limit
PAUSE = 1.0  # seconds between two page requests
RETRIES = 5

QUERY = """
SELECT ?item ?title ?id WHERE {
  ?item wdt:%s ?id .
  ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> ;
           schema:name ?title .
}
"""
PROPERTIES = {"P1550": "ORPHA", "P492": "OMIM"}  # Orphanet id, OMIM id


class Article(BaseModel):
    title: str
    wikidata: str  # Q-id
    orpha: list[str]  # ORPHA:n
    omim: list[str]  # OMIM:n
    pageid: int = 0
    revid: int = 0


def client() -> httpx.Client:
    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True)


def disease_articles(http: httpx.Client) -> list[Article]:
    """Every English article whose Wikidata item has an Orphanet or OMIM id (one query
    per property: together they exceed the query service's time limit)."""
    found: dict[str, Article] = {}
    for prop, prefix in PROPERTIES.items():
        r = http.get(SPARQL, params={"query": QUERY % prop, "format": "json"}, timeout=180)
        r.raise_for_status()
        for row in r.json()["results"]["bindings"]:
            title = row["title"]["value"]
            article = found.setdefault(
                title,
                Article(
                    title=title, wikidata=row["item"]["value"].rsplit("/", 1)[1], orpha=[], omim=[]
                ),
            )
            ids = article.orpha if prefix == "ORPHA" else article.omim
            disease = f"{prefix}:{row['id']['value']}"
            if disease not in ids:
                ids.append(disease)
    return sorted(found.values(), key=lambda a: a.title)


def with_revisions(articles: list[Article], http: httpx.Client) -> list[Article]:
    """The articles with their page and current revision ids; redirects followed,
    articles the API no longer has dropped."""
    out = []
    for start in range(0, len(articles), BATCH):
        batch = {a.title: a for a in articles[start : start + BATCH]}
        r = http.get(
            API,
            params={
                "action": "query",
                "prop": "revisions",
                "rvprop": "ids",
                "titles": "|".join(batch),
                "redirects": 1,
                "format": "json",
                "formatversion": 2,
            },
        )
        r.raise_for_status()
        data = r.json()["query"]
        renamed = {n["from"]: n["to"] for n in data.get("normalized", [])}
        renamed |= {d["from"]: d["to"] for d in data.get("redirects", [])}
        found = {p["title"]: p for p in data["pages"] if "revisions" in p}
        for title, article in batch.items():
            name = title
            while name in renamed:
                name = renamed[name]
            page = found.get(name)
            if page:
                out.append(
                    article.model_copy(
                        update={"pageid": page["pageid"], "revid": page["revisions"][0]["revid"]}
                    )
                )
    return merged(out)


def merged(articles: list[Article]) -> list[Article]:
    """One article per revision: titles that redirect to the same page (two Wikidata
    items, one article) become one, about the diseases of both."""
    by_revision: dict[int, Article] = {}
    for a in sorted(articles, key=lambda a: a.title):
        if (kept := by_revision.get(a.revid)) is None:
            by_revision[a.revid] = a.model_copy()
            continue
        kept.orpha += [d for d in a.orpha if d not in kept.orpha]
        kept.omim += [d for d in a.omim if d not in kept.omim]
    return list(by_revision.values())


def write_manifest(path: Path, articles: list[Article]) -> None:
    lines = [HEADER] + [
        f"{a.title}\t{a.pageid}\t{a.revid}\t{a.wikidata}\t{' '.join(a.orpha)}\t{' '.join(a.omim)}"
        for a in sorted(articles, key=lambda a: a.revid)
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> list[Article]:
    rows = path.read_text(encoding="utf-8").splitlines()[1:]
    out = []
    for row in rows:
        title, pageid, revid, wikidata, orpha, omim = row.split("\t")
        out.append(
            Article(
                title=title,
                pageid=int(pageid),
                revid=int(revid),
                wikidata=wikidata,
                orpha=orpha.split(),
                omim=omim.split(),
            )
        )
    return out


def _get(http: httpx.Client, url: str, params: dict[str, Any]) -> httpx.Response:
    """A GET that, told to slow down (429) or finding the server busy (503), waits as
    long as it is told (Retry-After; else 30 s, doubling) and tries again."""
    wait = 30.0
    for _ in range(RETRIES):
        r = http.get(url, params=params)
        if r.status_code not in (429, 503):
            r.raise_for_status()
            return r
        after = r.headers.get("retry-after", "")
        time.sleep(float(after) if after.isdigit() else wait)
        wait *= 2
    r.raise_for_status()
    return r


def html(revid: int, http: httpx.Client) -> str:
    """The rendered HTML of one revision."""
    r = _get(
        http,
        API,
        {
            "action": "parse",
            "oldid": revid,
            "prop": "text",
            "disableeditsection": 1,
            "format": "json",
            "formatversion": 2,
        },
    )
    return str(r.json()["parse"]["text"])


def fetched(path: Path) -> set[int]:
    """The revisions already in the pages file."""
    if not path.exists():
        return set()
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return {json.loads(line)["revid"] for line in f}


def fetch(articles: list[Article], path: Path, http: httpx.Client) -> Iterator[Article]:
    """Fetch every article not yet in the pages file, appending each as it comes (an
    interrupted run resumes); yields each one fetched."""
    have = fetched(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    for article in articles:
        if article.revid in have:
            continue
        time.sleep(PAUSE)
        page = {**article.model_dump(), "html": html(article.revid, http)}
        with gzip.open(path, "at", encoding="utf-8") as f:
            f.write(json.dumps(page, ensure_ascii=False) + "\n")
        have.add(article.revid)
        yield article


def pages(path: Path) -> Iterator[dict[str, object]]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

"""Pinning Wikipedia's articles by revision."""

from pathlib import Path

import httpx

from raredx.data import wikipedia
from raredx.data.wikipedia import Article


def test_revisions_follow_redirects_and_drop_missing_pages(tmp_path: Path) -> None:
    def reply(request: httpx.Request) -> httpx.Response:
        assert "raredx" in request.headers["user-agent"]  # who is asking, without an email
        return httpx.Response(
            200,
            json={
                "query": {
                    "redirects": [{"from": "Old name", "to": "Xyz syndrome"}],
                    "pages": [
                        {"title": "Xyz syndrome", "pageid": 5, "revisions": [{"revid": 42}]},
                        {"title": "Gone", "missing": True},
                    ],
                }
            },
        )

    http = httpx.Client(
        transport=httpx.MockTransport(reply), headers={"User-Agent": wikipedia.USER_AGENT}
    )
    listed = [
        Article(title="Old name", wikidata="Q1", orpha=["ORPHA:9001"], omim=[]),
        Article(title="Gone", wikidata="Q2", orpha=[], omim=["OMIM:690001"]),
    ]
    [found] = wikipedia.with_revisions(listed, http)
    assert (found.title, found.pageid, found.revid) == ("Old name", 5, 42)
    path = tmp_path / "revisions.tsv"
    wikipedia.write_manifest(path, [found])
    assert wikipedia.read_manifest(path) == [found]

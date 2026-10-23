"""The text index: hybrid search in an in-memory Qdrant, over the miniature texts."""

from pathlib import Path

import pytest

from raredx.knowledge.text_index import Embedder, Mode, TextIndex
from raredx.knowledge.texts import Passage


@pytest.mark.parametrize("mode", ["hybrid", "dense", "keyword"])
def test_each_mode_finds_the_passage_sharing_the_query_words(
    text_index: TextIndex[Passage], mode: Mode
) -> None:
    [(best, score), *_] = text_index.search("night blindness and hearing loss", 3, mode)
    assert best.disease_ids == ["OMIM:690002"]
    assert score > 0


def test_an_index_saved_and_loaded_searches_the_same(
    text_index: TextIndex[Passage], word_embedder: Embedder, tmp_path: Path
) -> None:
    embedder = word_embedder
    dense, sparse = embedder.passages([p.text for p in text_index.passages])
    TextIndex.save(tmp_path, text_index.passages, dense, sparse, {"sources": "test texts"})
    loaded = TextIndex.load(tmp_path, embedder, Passage)
    query = "absent menstruation"
    assert [p.source for p, _ in loaded.search(query, 2)] == [
        p.source for p, _ in text_index.search(query, 2)
    ]
    assert loaded.info["passages"] == len(text_index.passages)


@pytest.mark.parametrize("mode", ["hybrid", "dense", "keyword"])
def test_a_search_can_be_kept_to_some_diseases_and_away_from_others(
    text_index: TextIndex[Passage], mode: Mode
) -> None:
    query = "night blindness and hearing loss"
    [(best, _), *_] = text_index.search(query, 3, mode)
    hidden = best.disease_ids[0]
    assert all(
        hidden not in p.disease_ids
        for p, _ in text_index.search(query, 9, mode, hide_diseases=[hidden])
    )
    others = {d for p in text_index.passages for d in p.disease_ids} - {hidden}
    other = sorted(others)[0]
    assert {
        d for p, _ in text_index.search(query, 9, mode, only=[other]) for d in p.disease_ids
    } == {other}


def test_a_chunk_citing_a_hidden_paper_is_never_returned(word_embedder: Embedder) -> None:
    chunks = [
        Passage(
            text="night blindness",
            disease_ids=["OMIM:1"],
            disease_name="a",
            source="a",
            pmids=["PMID:7"],
        ),
        Passage(text="night blindness again", disease_ids=["OMIM:1"], disease_name="a", source="b"),
    ]
    dense, sparse = word_embedder.passages([c.text for c in chunks])
    index = TextIndex(chunks, dense, sparse, word_embedder, {})
    assert [p.source for p, _ in index.search("night blindness", 5, hide_pmids=["PMID:7"])] == ["b"]

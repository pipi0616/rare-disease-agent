"""The text index: hybrid search in an in-memory Qdrant, over the miniature texts."""

from pathlib import Path

import pytest

from raredx.knowledge.text_index import Embedder, Mode, TextIndex


@pytest.mark.parametrize("mode", ["hybrid", "dense", "keyword"])
def test_each_mode_finds_the_passage_sharing_the_query_words(
    text_index: TextIndex, mode: Mode
) -> None:
    [(best, score), *_] = text_index.search("night blindness and hearing loss", 3, mode)
    assert best.disease_ids == ["OMIM:690002"]
    assert score > 0


def test_an_index_saved_and_loaded_searches_the_same(
    text_index: TextIndex, word_embedder: Embedder, tmp_path: Path
) -> None:
    embedder = word_embedder
    dense, sparse = embedder.passages([p.text for p in text_index.passages])
    TextIndex.save(tmp_path, text_index.passages, dense, sparse, {"sources": "test texts"})
    loaded = TextIndex.load(tmp_path, embedder)
    query = "absent menstruation"
    assert [p.source for p, _ in loaded.search(query, 2)] == [
        p.source for p, _ in text_index.search(query, 2)
    ]
    assert loaded.info["passages"] == len(text_index.passages)

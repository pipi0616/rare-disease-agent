"""The second layer of the RAG evaluation, with a model that costs nothing."""

from typing import Any

from raredx.evals import rag, rag_answers
from raredx.knowledge.text_index import Embedder, TextIndex
from raredx.knowledge.texts import Passage
from raredx.llm import Budget, Tally


def test_closed_and_open_book_answers_are_scored_against_orphanet(
    word_embedder: Embedder, fake_llm: Any
) -> None:
    chunks = [
        Passage(
            text="Xyz syndrome — Genetic counseling: inherited in an autosomal recessive manner.",
            disease_ids=["OMIM:1"],
            disease_name="Xyz syndrome",
            source="a",
        ),
        Passage(
            text="Xyz syndrome causes hearing loss.",
            disease_ids=["OMIM:1"],
            disease_name="Xyz syndrome",
            source="b",
        ),
    ]
    dense, sparse = word_embedder.passages([c.text for c in chunks])
    index = TextIndex(chunks, dense, sparse, word_embedder, {})
    q = rag.Question(
        kind="inheritance",
        source="s",
        case_id="c",
        text="Xyz syndrome: mode of inheritance",
        disease="OMIM:1",
        accepted=["OMIM:1"],
        answer=[rag.INHERITANCE["Autosomal recessive"]],
        hide_pmids=[],
        hide_diseases=[],
    )
    llm = fake_llm(
        '{"inheritance": "autosomal dominant"}',  # closed book: wrong
        '{"inheritance": "autosomal recessive", "passages": [1, 2]}',  # right, grounded
    )
    [result] = rag_answers.run(index, [q], llm, "m", Budget(1.0), Tally(), workers=1)
    assert result.truth == ["autosomal recessive"] and result.retrieved_says
    assert (result.closed, result.open, result.grounded) == (
        "autosomal dominant",
        "autosomal recessive",
        True,
    )
    assert "Genetic counseling: inherited" in llm.requests[1]["messages"][1]["content"]
    s = rag_answers.summary([result])
    assert (
        s["closed"]["right"] == 0.0 and s["open"]["right"] == 1.0 and s["open"]["grounded"] == 1.0
    )

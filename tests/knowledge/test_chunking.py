"""The five ways of cutting a document: what each chunk carries."""

from raredx.knowledge import chunking
from raredx.knowledge.corpus import Document, Paragraph, Section

LONG = " ".join(f"word{i}" for i in range(400))  # about 3,000 characters


def document() -> Document:
    return Document(
        id="T:xyz",
        source="test",
        title="Xyz Syndrome",
        disease_ids=["OMIM:690001"],
        sections=[
            Section(title="Diagnosis", paragraphs=[Paragraph(text=LONG, pmids=["PMID:1"])]),
            Section(
                title="Genetic Counseling", paragraphs=[Paragraph(text="Autosomal recessive.")]
            ),
        ],
        url="https://example.org/xyz",
    )


def test_every_strategy_keeps_the_text_the_diseases_and_the_papers() -> None:
    for strategy in chunking.STRATEGIES:
        chunks = chunking.chunk(document(), strategy)
        assert all(c.disease_ids == ["OMIM:690001"] and c.doc == "T:xyz" for c in chunks)
        assert all(len(c.text) <= chunking.SIZE + 60 for c in chunks)  # 60: a header
        assert any("PMID:1" in c.pmids for c in chunks)
        assert any("Autosomal recessive" in (c.parent or c.text) for c in chunks), strategy


def test_a_section_chunk_never_mixes_sections_and_cites_only_its_own_paragraphs() -> None:
    chunks = chunking.chunk(document(), "section")
    last = [c for c in chunks if "Autosomal" in c.text]
    assert len(last) == 1 and last[0].section == "Genetic Counseling" and last[0].pmids == []
    assert "word" not in last[0].text


def test_the_context_header_and_the_parent() -> None:
    [*_, counselling] = chunking.chunk(document(), "section+context")
    assert counselling.text == "Xyz Syndrome — Genetic Counseling: Autosomal recessive."
    small = chunking.chunk(document(), "parent")
    assert all(c.parent.startswith("Xyz Syndrome — ") for c in small)
    assert all(len(c.text) < len(c.parent) or "Autosomal" in c.text for c in small)

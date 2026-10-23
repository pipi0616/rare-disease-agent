"""Cutting documents into chunks: five ways, compared in chapter 33.

| strategy        | how                                                               |
|-----------------|-------------------------------------------------------------------|
| fixed           | every SIZE characters (at a space), OVERLAP shared with the next; |
|                 | the document's structure ignored — the naive baseline             |
| recursive       | LangChain's RecursiveCharacterTextSplitter over the whole text:   |
|                 | paragraph breaks first, then lines, then words — the usual default|
| section         | the same, but within one section at a time: a chunk never mixes   |
|                 | two sections                                                      |
| section+context | section, each chunk led by "Title — Section:" so that it reads on |
|                 | its own (a contextual chunk header)                               |
| parent          | section+context chunks are split again into small ones (SMALL     |
|                 | characters); the small one is what is searched, the section chunk |
|                 | containing it is what is returned ("small-to-big")                |

Every chunk keeps what masking needs: the PubMed ids cited by any paragraph it
overlaps (for parent, the parent's), and the diseases of its document.
"""

from typing import Literal

from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter

from raredx.knowledge.corpus import Document
from raredx.knowledge.texts import Passage

Strategy = Literal["fixed", "recursive", "section", "section+context", "parent"]
STRATEGIES: tuple[Strategy, ...] = ("fixed", "recursive", "section", "section+context", "parent")
SIZE, OVERLAP, SMALL, SMALL_OVERLAP = 1000, 150, 300, 50
BREAK = "\n\n"


def _splitter(strategy: Strategy) -> CharacterTextSplitter | RecursiveCharacterTextSplitter:
    if strategy == "fixed":
        return CharacterTextSplitter(
            separator=" ", chunk_size=SIZE, chunk_overlap=OVERLAP, add_start_index=True
        )
    return RecursiveCharacterTextSplitter(
        chunk_size=SIZE, chunk_overlap=OVERLAP, add_start_index=True
    )


def _pieces(
    paragraphs: list[tuple[str, list[str]]], strategy: Strategy
) -> list[tuple[str, list[str]]]:
    """A run of paragraphs, joined and split: each piece with the papers cited by the
    paragraphs it overlaps."""
    spans, at = [], 0
    for text, pmids in paragraphs:
        spans.append((at, at + len(text), pmids))
        at += len(text) + len(BREAK)
    whole = BREAK.join(text for text, _ in paragraphs)
    out = []
    for piece in _splitter(strategy).create_documents([whole]):
        start = piece.metadata["start_index"]
        end = start + len(piece.page_content)
        cited = sorted({p for s, e, pmids in spans if s < end and e > start for p in pmids})
        out.append((piece.page_content, cited))
    return out


def chunk(doc: Document, strategy: Strategy) -> list[Passage]:
    """The document's chunks under one strategy."""

    def passage(text: str, section: str, pmids: list[str], parent: str = "") -> Passage:
        return Passage(
            text=text,
            disease_ids=doc.disease_ids,
            disease_name=doc.title,
            source=doc.url,
            doc=doc.id,
            section=section,
            pmids=pmids,
            parent=parent,
        )

    if strategy in ("fixed", "recursive"):  # the document as one text, headings as lines
        paragraphs: list[tuple[str, list[str]]] = [(doc.title, [])]
        for section in doc.sections:
            if section.title:
                paragraphs.append((section.title, []))
            paragraphs += [(p.text, p.pmids) for p in section.paragraphs]
        return [passage(text, "", pmids) for text, pmids in _pieces(paragraphs, strategy)]

    out = []
    for section in doc.sections:
        pieces = _pieces([(p.text, p.pmids) for p in section.paragraphs], "section")
        header = f"{doc.title} — {section.title}: " if section.title else f"{doc.title}: "
        for text, pmids in pieces:
            if strategy == "section":
                out.append(passage(text, section.title, pmids))
                continue
            whole = header + text
            if strategy == "section+context":
                out.append(passage(whole, section.title, pmids))
                continue
            small = RecursiveCharacterTextSplitter(chunk_size=SMALL, chunk_overlap=SMALL_OVERLAP)
            for part in small.split_text(text):
                out.append(passage(header + part, section.title, pmids, parent=whole))
    return out

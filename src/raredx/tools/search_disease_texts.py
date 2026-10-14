"""T6 · search disease texts: what Orphanet and MedlinePlus write, retrieved for a question.

The standard RAG tool: the agent writes a query in its own words — the
patient's key findings, or a disease's name — and gets back the passages that
match best, each with the OMIM diseases it is about and its source, to cite.
Retrieval is hybrid (meaning and keywords, fused in Qdrant; see text_index).

The texts do not cite their papers, so they cannot be masked by reference as
the HPO annotations are. Instead, while a paper is masked, every passage about
a disease HPO knows only from that paper is hidden: such a description most
likely rests on the same paper — in evaluation, the one the case comes from.
"""

from typing import Annotated

import mlflow
from mlflow.entities import SpanType
from pydantic import BaseModel, Field, validate_call

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.knowledge.text_index import Mode, TextIndex
from raredx.knowledge.texts import Passage

MARGIN = 20  # passages fetched beyond top_k, so hiding a few still leaves top_k


class TextHit(BaseModel):
    disease_ids: list[str] = Field(description="The OMIM diseases the passage is about")
    disease_name: str
    text: str
    source: str = Field(description="Where the passage is from, to cite")


class TextHits(BaseModel):
    hits: list[TextHit] = Field(description="Best match first")
    searched: int = Field(description="Passages searched")


class SearchDiseaseTexts:
    name = "search_disease_texts"
    title = "Search disease descriptions"

    def __init__(self, index: TextIndex[Passage], hpo: HPO) -> None:
        self.index = index
        self.hpo = hpo

    def ranked(self, query: str, limit: int, mode: Mode = "hybrid") -> list[Passage]:
        """The best passages for the query, those hidden by the mask left out."""
        hidden = self.hpo.known_only_from(masking.current())
        found = self.index.search(query, limit + MARGIN, mode)
        return [p for p, _ in found if not hidden.intersection(p.disease_ids)][:limit]

    @mlflow.trace(name="search_disease_texts", span_type=SpanType.TOOL)
    @validate_call
    def __call__(
        self,
        query: Annotated[
            str,
            Field(
                min_length=3,
                max_length=500,
                description="What to look for, in words: findings, or a disease's name",
            ),
        ],
        top_k: Annotated[int, Field(ge=1, le=20, description="How many passages to return")] = 5,
    ) -> TextHits:
        """Search what Orphanet and MedlinePlus Genetics write about diseases, in your
        own words: the patient's key findings, or a disease's name.

        Use it to read how a candidate is described, or to find diseases whose
        description fits findings the other tools weigh poorly. Each passage names
        the OMIM diseases it is about and its source, to cite.
        """
        hidden = self.hpo.known_only_from(masking.current())
        return TextHits(
            hits=[
                TextHit(
                    disease_ids=p.disease_ids,
                    disease_name=p.disease_name,
                    text=p.text,
                    source=p.source,
                )
                for p in self.ranked(query, top_k)
            ],
            searched=sum(not hidden.intersection(p.disease_ids) for p in self.index.passages),
        )

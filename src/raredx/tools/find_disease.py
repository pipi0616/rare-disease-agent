"""Find a disease by name: from the name a model has in mind to the id the other tools take.

A model remembers diseases by name; it often gets their OMIM numbers wrong.
This tool closes that gap, so an agent can check a disease it suspects itself,
not only those rank_diseases proposed. Names are matched fuzzily (rapidfuzz's
WRatio: word order, partial names and punctuation are forgiven), against every
OMIM disease in the HPO release.

A disease described only in a masked paper is not found: its very name comes
from that paper (in evaluation, the case's own).
"""

from typing import Annotated

import mlflow
from mlflow.entities import SpanType
from pydantic import BaseModel, Field, validate_call
from rapidfuzz import fuzz, process, utils

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO


class NamedDisease(BaseModel):
    disease_id: str
    disease_name: str
    similarity: int = Field(description="How closely the name matches, 0–100")


class Found(BaseModel):
    matches: list[NamedDisease] = Field(description="Closest names first")


class FindDisease:
    name = "find_disease"
    title = "Find a disease by name"

    def __init__(self, hpo: HPO) -> None:
        self.hpo = hpo

    @mlflow.trace(name="find_disease", span_type=SpanType.TOOL)
    @validate_call
    def __call__(
        self,
        name: Annotated[
            str, Field(min_length=3, description="A disease name, e.g. Aarskog-Scott syndrome")
        ],
        limit: Annotated[int, Field(ge=1, le=20, description="How many names to return")] = 5,
    ) -> Found:
        """Find OMIM diseases by name, to get the id of a disease you have in mind.

        Use it before check_match or lookup_disease on a disease rank_diseases did not
        propose. Several close matches can come back (numbered subtypes, say); read
        the names.
        """
        hidden = self.hpo.known_only_from(masking.current())
        names = {d: n for d, n in self.hpo.names.items() if d not in hidden}
        hits = process.extract(
            name, names, scorer=fuzz.WRatio, processor=utils.default_process, limit=None
        )
        hits.sort(key=lambda h: (-h[1], h[2]))  # equal scores in id order, for repeatability
        return Found(
            matches=[
                NamedDisease(disease_id=d, disease_name=self.hpo.names[d], similarity=round(s))
                for _, s, d in hits[:limit]
            ]
        )

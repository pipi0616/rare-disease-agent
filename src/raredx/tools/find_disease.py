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

from raredx.evals.scoring import normalize_omim
from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO

# How closely a guessed name must match HPO's (WRatio, 0–100) to stand for a number HPO
# does not know. Not 80: on recorded direct answers (dev-200, HMS, RAMEDIS), names sharing
# only "syndrome" scored over 80, and replacing the numbers the model wrote by the closest
# names lost more cases than it found, at any threshold. So a number HPO knows is kept,
# and a name is looked up only for one it does not (2–11% of them).
NAME_MATCH = 90


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


def resolve(written_id: str | None, name: str, find: FindDisease) -> str | None:
    """The HPO disease a model's guess means: the id it wrote, when HPO knows it; else
    the disease of the closest name, when close (NAME_MATCH); else none. A disease the
    mask hides is unknown, as everywhere."""
    hpo = find.hpo
    written = normalize_omim(written_id)
    if written in hpo.names and written not in hpo.known_only_from(masking.current()):
        return written
    name = name.strip()
    found = find(name, limit=1).matches if len(name) >= 3 else []
    if found and found[0].similarity >= NAME_MATCH:
        return found[0].disease_id
    return None

"""The ids the tools take, and the error for a disease id that does not exist."""

from typing import Annotated

from pydantic import StringConstraints

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO

HpoId = Annotated[str, StringConstraints(pattern=r"^HP:\d{7}$")]
# A disease as the tools name it: an OMIM entry, or an Orphanet one (ORPHA).
DiseaseId = Annotated[str, StringConstraints(pattern=r"^(OMIM:\d{6}|ORPHA:\d+)$")]


class UnknownDisease(LookupError):
    """The id is well formed, but this HPO release has no such disease."""


def require_disease(hpo: HPO, disease_id: str) -> str:
    """The disease the id names here (an Orphanet code merged into an OMIM disease
    names that disease); an error the model can act on when there is none.

    While a paper is masked, a disease HPO knows only from that paper does not exist
    either, and the error says exactly what it says for any unknown id: nothing tells
    the model that something was hidden."""
    here = hpo.canonical(disease_id)
    if here is None or here in hpo.known_only_from(masking.current()):
        raise UnknownDisease(
            f"{disease_id} is not a disease in HPO {hpo.release}; "
            "use an id that rank_diseases returned"
        )
    return here

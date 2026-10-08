"""The ids the tools take, and the error for a disease id that does not exist."""

from typing import Annotated

from pydantic import StringConstraints

from raredx.knowledge.hpo import HPO

HpoId = Annotated[str, StringConstraints(pattern=r"^HP:\d{7}$")]
OmimId = Annotated[str, StringConstraints(pattern=r"^OMIM:\d{6}$")]


class UnknownDisease(LookupError):
    """The id is well formed, but this HPO release has no such disease."""


def require_disease(hpo: HPO, disease_id: str) -> None:
    """Raise an error the model can act on when the disease is not in the release."""
    if disease_id not in hpo.names:
        raise UnknownDisease(
            f"{disease_id} is not a disease in HPO {hpo.release}; "
            "use an id that rank_diseases returned"
        )

"""Shared test helpers."""

from collections.abc import Callable
from typing import Any

import pytest

from raredx.data.cases import Case


@pytest.fixture
def make_case() -> Callable[..., Case]:
    """A Case with sensible defaults; override any field by keyword."""

    def factory(case_id: str, **fields: Any) -> Case:
        values: dict[str, Any] = {
            "id": case_id,
            "cohort": "X",
            "hpo_ids": ["HP:0000365"],
            "hpo_labels": ["Hearing impairment"],
            "disease_id": "OMIM:621101",
            "disease_label": "Perrault syndrome 7",
            "gene": "DAP3",
            "variants": [],
            "pmid": f"PMID:{case_id}",
            "sex": None,
            "split": "design",
        }
        values.update(fields)
        return Case.model_validate(values)

    return factory

"""Shared test helpers."""

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from raredx.data.cases import Case
from raredx.knowledge.hpo import HPO, load

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True, scope="session")
def mlflow_store(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Whatever a test traces goes to a throwaway store, never the project's.

    MLflow's defaults are mlflow.db and mlruns/ in the working directory: the
    real ones, when the tests run from the project root. Tests that build their
    own store (the harness tests) point MLflow elsewhere again.
    """
    import mlflow  # here, not at the top: raredx must be imported first (mlflow_setup)

    root = tmp_path_factory.mktemp("mlflow")
    mlflow.set_tracking_uri(f"sqlite:///{root / 'mlflow.db'}")
    experiment_id = mlflow.create_experiment("tests", artifact_location=root.as_uri())
    mlflow.set_experiment(experiment_id=experiment_id)


@pytest.fixture(scope="session")
def hpo() -> HPO:
    """A miniature HPO release (tests/fixtures/hpo): 18 terms, 5 OMIM diseases.

    hpo3 holds one ontology per process, so every test shares this one, and no
    test may load the real release.
    """
    return load(FIXTURES / "hpo")


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


class FakeLLM:
    """Stands in for OpenAI(): returns the replies given, in turn; records every request."""

    def __init__(self, *replies: str) -> None:
        self.replies = list(replies)
        self.requests: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **request: Any) -> Any:
        self.requests.append(request)
        message = SimpleNamespace(content=self.replies.pop(0))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.fixture
def fake_llm() -> type[FakeLLM]:
    """A model client that costs nothing: FakeLLM(reply, ...)."""
    return FakeLLM

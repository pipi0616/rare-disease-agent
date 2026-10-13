"""Shared test helpers."""

import itertools
import re
import zlib
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult

from raredx.data.cases import Case
from raredx.knowledge import texts
from raredx.knowledge.hpo import HPO, load
from raredx.knowledge.text_index import TextIndex

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


@pytest.fixture
def patients(make_case: Callable[..., Case]) -> list[Case]:
    """A small bank of published patients over the miniature release, one paper each."""
    snhl, bilateral, amenorrhea = "HP:0000407", "HP:0008619", "HP:0000786"
    rod_cone, seizure = "HP:0000510", "HP:0001250"
    rows = [
        ("p1", [snhl, amenorrhea], "OMIM:690001", "Hearing-ovarian syndrome", "GENEA"),
        ("p2", [bilateral, amenorrhea], "OMIM:690001", "Hearing-ovarian syndrome", "GENEA"),
        ("p3", [snhl, rod_cone], "OMIM:690002", "Hearing-retina syndrome", "GENEB"),
        ("p4", [seizure], "OMIM:690003", "Seizure disorder", "GENEC"),
        # A disease HPO has not annotated: the bank still knows its patient.
        ("p5", [snhl, amenorrhea, seizure], "OMIM:699999", "Unannotated syndrome", "GENEZ"),
    ]
    return [
        make_case(
            case_id,
            hpo_ids=terms,
            hpo_labels=terms,
            disease_id=disease,
            disease_label=label,
            gene=gene,
            pmid=f"PMID:200{case_id[1:]}",
        )
        for case_id, terms, disease, label, gene in rows
    ]


class WordEmbedder:
    """Stands in for the embedding models: a vector of word counts, dense and sparse
    alike. No download, no model; texts sharing words come out close."""

    DIM = 256

    def _counts(self, text: str) -> Counter[int]:
        return Counter(
            zlib.crc32(w.encode()) % self.DIM for w in re.findall(r"[a-z]+", text.lower())
        )

    def passages(self, texts: list[str]) -> tuple[np.ndarray, list[tuple[list[int], list[float]]]]:
        rows = [self.query(t) for t in texts]
        return np.array([r[0] for r in rows], dtype=np.float32), [r[1] for r in rows]

    def query(self, text: str) -> tuple[list[float], tuple[list[int], list[float]]]:
        counts = self._counts(text)
        dense = [float(counts.get(i, 0)) for i in range(self.DIM)]
        indices = sorted(counts)
        return dense, (indices, [float(counts[i]) for i in indices])


@pytest.fixture(scope="session")
def word_embedder() -> WordEmbedder:
    return WordEmbedder()


@pytest.fixture(scope="session")
def text_index() -> TextIndex:
    """The miniature disease texts (tests/fixtures/texts), indexed with WordEmbedder."""
    passages = texts.read(FIXTURES / "texts", FIXTURES / "texts")
    embedder = WordEmbedder()
    dense, sparse = embedder.passages([p.text for p in passages])
    return TextIndex(passages, dense, sparse, embedder, {"sources": "test texts"})


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


OFFERED: list[list[str]] = []  # the tools offered to a ScriptedModel, call by call
RECEIVED: list[list[BaseMessage]] = []  # the messages it was sent, call by call


class ScriptedModel(GenericFakeChatModel):
    """Stands in for the chat model of an agent: plays the given moves, noting what it
    was offered and sent. The tools, the middleware and the final answer stay real."""

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedModel":
        OFFERED.append([t.name for t in tools])
        return self

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        RECEIVED.append(list(messages))
        return super()._generate(messages, *args, **kwargs)


_ids = itertools.count()


def call(tool: str, **args: Any) -> AIMessage:
    """One move: a new message each time, with its own tool-call id, as a real model sends."""
    tool_call = {"name": tool, "args": args, "id": f"{tool}-{next(_ids)}", "type": "tool_call"}
    return AIMessage(content="", tool_calls=[tool_call])


def answer(*diagnoses: tuple[str, str, str]) -> AIMessage:
    """The final move: the agent's answer, as (disease id, name, reason) rows."""
    rows = [{"disease_id": d, "disease_name": n, "reason": r} for d, n, r in diagnoses]
    return call("FinalAnswer", diagnoses=rows)

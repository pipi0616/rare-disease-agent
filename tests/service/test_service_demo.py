"""The demo page, run by Streamlit's own test harness against the service in process:
page, client, HTTP layer and agent together, with a scripted model."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx2
import pytest
import streamlit as st
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

import raredx.service.client
from conftest import ScriptedModel, answer
from raredx.agent import Agent
from raredx.data.cases import Case
from raredx.knowledge.hpo import HPO
from raredx.service import demo, examples
from raredx.service.app import create_app
from raredx.service.client import Client
from raredx.service.diagnoser import Diagnoser
from raredx.tools.find_similar_patients import FindSimilarPatients
from raredx.tools.rank_candidate_genes import RankCandidateGenes

PAGE = str(Path(demo.__file__))
SNHL, AMENORRHEA = "HP:0000407", "HP:0000786"
FITS = ("OMIM:690001", "Hearing-ovarian syndrome", "explains both findings")


@pytest.fixture
def page(
    hpo: HPO, patients: list[Case], make_case: Callable[..., Case], monkeypatch: pytest.MonkeyPatch
) -> Iterator[Callable[..., AppTest]]:
    """The page over a service with one example patient and a scripted model (or none)."""

    def build(*moves: Any) -> AppTest:
        agent = with_genes = None
        if moves:
            model = ScriptedModel(messages=iter(moves))
            bank = FindSimilarPatients(hpo, patients, "test bank")
            tools = [bank, RankCandidateGenes(hpo)]
            agent = Agent(model, "fake-model", hpo, seeded=True, extra_tools=[bank])
            with_genes = Agent(model, "fake-model", hpo, seeded=True, extra_tools=tools)
        case = make_case(
            examples.listed()[0][0],
            hpo_ids=[SNHL, AMENORRHEA],
            hpo_labels=["Sensorineural hearing impairment", "Primary amenorrhea"],
            disease_id="OMIM:690001",
            disease_label="Hearing-ovarian syndrome",
            gene=None,
            pmid="PMID:2001",
        )
        app = create_app(
            Diagnoser(hpo, agent=agent, agent_with_genes=with_genes),
            examples=examples.load([case], hpo),
        )
        http = TestClient(app)
        monkeypatch.setattr(raredx.service.client, "Client", lambda *a, **k: Client(http=http))
        return AppTest.from_file(PAGE, default_timeout=60)

    st.cache_resource.clear()
    yield build
    st.cache_resource.clear()


def texts(elements: Any) -> str:
    return "\n".join(str(e.value) for e in elements)


def test_an_example_is_diagnosed_and_its_published_diagnosis_placed(
    page: Callable[..., AppTest],
) -> None:
    at = page(answer(FITS)).run()
    assert not at.exception
    assert at.selectbox[0].options[0] == f"Example 1 · {examples.listed()[0][1]}"
    assert "Primary amenorrhea `HP:0000786`" in texts(at.markdown)
    assert "fake-model" in texts(at.sidebar.markdown)

    at.button(key="diagnose").click().run()
    assert not at.exception
    assert "Answered by the agent: 1 model calls" in texts(at.success)
    assert "**Hearing-ovarian syndrome** (OMIM:690001) — ranked **#1** here" in texts(at.info)
    shown = texts(at.markdown)
    assert "Phenotype tools: 5 diseases ranked" in shown  # the steps, as they came
    assert "Model, turn 1: gives its answer" in shown
    assert "**Explains 2 of 2 findings**" in shown  # the evidence of the first diagnosis
    assert at.dataframe[0].value["Disease"][0] == "Hearing-ovarian syndrome"


def test_without_a_model_the_page_says_the_fallback_answered(page: Callable[..., AppTest]) -> None:
    at = page().run()
    assert "No model" in texts(at.sidebar.warning)
    at.button(key="diagnose").click().run()
    assert not at.exception
    assert "Answered without the model — no model is configured" in texts(at.warning)


def test_a_patient_can_be_entered_and_a_wrong_term_is_explained(
    page: Callable[..., AppTest],
) -> None:
    at = page().run()
    at.selectbox[0].select(demo.OWN).run()
    assert at.button(key="diagnose").disabled  # nothing to send yet
    at.text_area(key="own_terms").input(f"{SNHL}, HP:1234567").run()
    at.button(key="diagnose").click().run()
    assert "not HPO terms in release 2099-01-01: HP:1234567" in texts(at.error)
    at.text_area(key="own_terms").input(f"{SNHL}\n{AMENORRHEA}").run()
    at.button(key="diagnose").click().run()
    assert not at.exception and at.dataframe[0].value["OMIM"][0] == "OMIM:690001"


def test_the_page_says_so_when_the_service_is_not_there(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Unreachable:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def system(self) -> None:
            raise httpx2.ConnectError("connection refused")

    st.cache_resource.clear()
    monkeypatch.setattr(raredx.service.client, "Client", Unreachable)
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    st.cache_resource.clear()
    assert not at.exception
    assert "is not answering (ConnectError)" in texts(at.error)
    assert "raredx serve" in texts(at.error)

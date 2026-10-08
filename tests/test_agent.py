"""The agent, driven by a scripted fake model on the miniature HPO release: no network, no cost.

The fake model plays the agent's moves; the tools, the middleware and the final
answer are real.
"""

import itertools
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage

from raredx.agent import MAX_MODEL_CALLS, Agent, NoFinalAnswer, as_langchain_tool
from raredx.data.cases import Case
from raredx.evals.systems import question_of
from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.rank_diseases import RankDiseases

OFFERED: list[list[str]] = []  # the tools offered to the model, call by call


class ScriptedModel(GenericFakeChatModel):
    """A fake chat model that plays the given moves, noting which tools it was offered."""

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedModel":
        OFFERED.append([t.name for t in tools])
        return self


_ids = itertools.count()


def call(tool: str, **args: Any) -> AIMessage:
    """One move: a new message each time, with its own tool-call id, as a real model sends."""
    tool_call = {"name": tool, "args": args, "id": f"{tool}-{next(_ids)}", "type": "tool_call"}
    return AIMessage(content="", tool_calls=[tool_call])


def answer(*diagnoses: tuple[str, str, str]) -> AIMessage:
    rows = [{"disease_id": d, "disease_name": n, "reason": r} for d, n, r in diagnoses]
    return call("FinalAnswer", diagnoses=rows)


def agent(hpo: HPO, moves: Iterator[AIMessage]) -> Agent:
    return Agent(ScriptedModel(messages=moves), "deepseek-flash", hpo)


@pytest.fixture
def case(make_case: Callable[..., Case]) -> Case:
    return make_case(
        "1", hpo_ids=["HP:0000407", "HP:0000786"], hpo_labels=["SNHL", "Primary amenorrhea"]
    )


def test_the_agent_investigates_then_answers_with_reasons(hpo: HPO, case: Case) -> None:
    moves = iter(
        [
            call("rank_diseases", hpo_ids=case.hpo_ids),
            call("check_match", hpo_ids=case.hpo_ids, disease_id="OMIM:690001"),
            answer(
                ("OMIM:690001", "Hearing-ovarian syndrome", "explains both findings"),
                ("690001", "Hearing-ovarian syndrome", "a repeat"),  # dropped
                ("not an id", "Something", "unusable"),  # dropped
                ("OMIM:690004", "Amenorrhea known from one paper", "explains one"),
            ),
        ]
    )
    answers = agent(hpo, moves).predict(question_of(case))
    assert [(c.disease_id, c.gene, c.reason) for c in answers] == [
        ("OMIM:690001", "GENEA", "explains both findings"),  # its one gene, from HPO
        ("OMIM:690004", None, "explains one"),
    ]


def test_an_unknown_disease_comes_back_to_the_model_as_a_message(hpo: HPO, case: Case) -> None:
    moves = iter(
        [
            call("lookup_disease", disease_id="OMIM:999999"),
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits")),
        ]
    )
    result = agent(hpo, moves).graph.invoke({"messages": [HumanMessage("a patient")]})
    [error] = [m for m in result["messages"] if m.type == "tool" and m.name == "lookup_disease"]
    assert "OMIM:999999 is not a disease" in str(error.content)
    assert result["structured_response"].diagnoses[0].disease_id == "OMIM:690001"


def test_on_its_last_turn_the_model_is_offered_only_the_final_answer(hpo: HPO, case: Case) -> None:
    OFFERED.clear()
    investigating = [
        call("rank_diseases", hpo_ids=case.hpo_ids) for _ in range(MAX_MODEL_CALLS - 1)
    ]
    final = answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits"))
    answers = agent(hpo, iter([*investigating, final])).predict(question_of(case))
    assert [c.disease_id for c in answers] == ["OMIM:690001"]
    assert len(OFFERED) == MAX_MODEL_CALLS
    assert OFFERED[0] == [
        "rank_diseases",
        "check_match",
        "lookup_disease",
        "find_disease",
        "FinalAnswer",
    ]
    assert OFFERED[-1] == ["FinalAnswer"]


def test_a_model_that_still_does_not_answer_stops_at_the_limit_and_fails(
    hpo: HPO, case: Case
) -> None:
    endless = (call("rank_diseases", hpo_ids=case.hpo_ids) for _ in itertools.count())
    with pytest.raises(NoFinalAnswer, match=f"{MAX_MODEL_CALLS} model calls"):
        agent(hpo, endless).predict(question_of(case))


def test_the_evaluation_mask_reaches_the_tools_the_agent_calls(hpo: HPO, case: Case) -> None:
    moves = iter(
        [
            call("rank_diseases", hpo_ids=["HP:0000786"]),
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits")),
        ]
    )
    with masking.masked(["PMID:1004"]):
        result = agent(hpo, moves).graph.invoke({"messages": [HumanMessage("a patient")]})
    [ranking] = [m for m in result["messages"] if m.type == "tool" and m.name == "rank_diseases"]
    assert "OMIM:690001" in str(ranking.content) and "OMIM:690004" not in str(ranking.content)


def test_the_tools_reach_the_model_with_their_own_schemas(hpo: HPO) -> None:
    arguments = as_langchain_tool(RankDiseases(hpo)).args
    assert set(arguments) == {"hpo_ids", "top_k"}  # no self
    assert arguments["hpo_ids"]["items"]["pattern"] == r"^HP:\d{7}$"
    params = agent(hpo, iter([])).params()
    assert params["tools"] == "rank_diseases, check_match, lookup_disease, find_disease"
    assert (params["prompt_version"], params["max_model_calls"]) == ("agent-v2", MAX_MODEL_CALLS)

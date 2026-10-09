"""The agent, driven by a scripted fake model on the miniature HPO release: no network, no cost.

The fake model plays the agent's moves; the tools, the middleware and the final
answer are real.
"""

import itertools
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatResult

from raredx.agent import FILLED, LAST_TURN, MAX_MODEL_CALLS, Agent, NoFinalAnswer, as_langchain_tool
from raredx.baselines.rank_then_check import RankThenCheck
from raredx.data.cases import Case
from raredx.evals.systems import question_of
from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.find_similar_patients import FindSimilarPatients
from raredx.tools.rank_candidate_genes import RankCandidateGenes
from raredx.tools.rank_diseases import RankDiseases

OFFERED: list[list[str]] = []  # the tools offered to the model, call by call
RECEIVED: list[list[BaseMessage]] = []  # the messages it was sent, call by call


class ScriptedModel(GenericFakeChatModel):
    """A fake chat model that plays the given moves, noting what it was offered and sent."""

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
    RECEIVED.clear()
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
    assert RECEIVED[-1][-1].content == LAST_TURN  # and it is told so
    assert all(m.content != LAST_TURN for m in RECEIVED[-2])  # only on the last turn


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
    assert (params["prompt_version"], params["max_model_calls"]) == ("agent-v3", MAX_MODEL_CALLS)


def seeded(hpo: HPO, moves: Iterator[AIMessage]) -> Agent:
    return Agent(ScriptedModel(messages=moves), "deepseek-flash", hpo, seeded=True)


def test_the_seeded_agent_starts_from_the_tools_evidence(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    moves = iter([answer(("OMIM:690001", "Hearing-ovarian syndrome", "explains both"))])
    seeded(hpo, moves).predict(question_of(case))
    system, first = RECEIVED[0][0], RECEIVED[0][1]
    assert "The tools have already ranked every disease" in str(system.content)
    assert "SNHL (HP:0000407)" in str(first.content)  # the ids it needs to call the tools
    assert "Candidates, in the order the phenotype tools rank them:" in str(first.content)
    assert "explains 2 of 2 findings" in str(first.content)


def test_a_short_answer_is_filled_from_the_tools_order(hpo: HPO, case: Case) -> None:
    moves = iter([answer(("OMIM:690004", "Amenorrhea known from one paper", "my pick"))])
    answers = seeded(hpo, moves).predict(question_of(case))
    tools_order = [
        m.disease_id
        for m, _ in RankThenCheck(RankDiseases(hpo), CheckMatch(hpo)).ordered(question_of(case))
    ]
    assert [c.disease_id for c in answers] == ["OMIM:690004"] + [
        d for d in tools_order if d != "OMIM:690004"
    ]
    assert answers[0].reason == "my pick"
    assert all(c.reason == FILLED for c in answers[1:])


def test_the_plain_agent_does_not_fill(hpo: HPO, case: Case) -> None:
    moves = iter([answer(("OMIM:690004", "Amenorrhea known from one paper", "my pick"))])
    assert len(agent(hpo, moves).predict(question_of(case))) == 1


def test_the_seeded_agent_records_its_seed_and_fill(hpo: HPO) -> None:
    system = seeded(hpo, iter([]))
    params = system.params()
    assert system.name == "seeded-agent" and params["prompt_version"] == "seeded-v1"
    assert (params["seed"], params["fill"]) == ("rank-then-check top 10", "the tools' order")


def test_an_extra_tool_is_offered_and_named_in_the_prompt(
    hpo: HPO, case: Case, patients: list[Case]
) -> None:
    OFFERED.clear()
    RECEIVED.clear()
    similar = FindSimilarPatients(hpo, patients, "test bank")
    moves = iter(
        [
            call("find_similar_patients", hpo_ids=case.hpo_ids),
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "similar patients have it")),
        ]
    )
    system = Agent(ScriptedModel(messages=moves), "deepseek-flash", hpo, extra_tools=[similar])
    system.predict(question_of(case))
    assert "find_similar_patients" in OFFERED[0]
    assert "- find_similar_patients: published patients" in str(RECEIVED[0][0].content)
    [found] = [m for m in RECEIVED[-1] if m.type == "tool"]
    assert "PMID:2001" in str(found.content)
    assert system.params()["patient_bank"] == "test bank"


def test_without_the_extra_tool_the_prompt_does_not_mention_it(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    moves = iter([answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits"))])
    agent(hpo, moves).predict(question_of(case))
    assert "find_similar_patients" not in str(RECEIVED[0][0].content)


def test_a_tool_without_a_prompt_guide_is_refused(hpo: HPO) -> None:
    class Unguided:
        name = "mystery_tool"

    with pytest.raises(ValueError, match="mystery_tool"):
        Agent(ScriptedModel(messages=iter([])), "deepseek-flash", hpo, extra_tools=[Unguided()])


def test_candidate_genes_reach_the_model_and_the_gene_tool_is_offered(hpo: HPO, case: Case) -> None:
    OFFERED.clear()
    RECEIVED.clear()
    moves = iter(
        [
            call("rank_candidate_genes", hpo_ids=case.hpo_ids, genes=["GENEA", "GENEE"]),
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "GENEA's disease fits")),
        ]
    )
    system = Agent(
        ScriptedModel(messages=moves), "deepseek-flash", hpo, extra_tools=[RankCandidateGenes(hpo)]
    )
    question = question_of(case).model_copy(update={"candidate_genes": ["GENEA", "GENEE"]})
    system.predict(question)
    assert "rank_candidate_genes" in OFFERED[0]
    assert "Candidate genes from sequencing (at most one is causal): GENEA, GENEE" in str(
        RECEIVED[0][1].content
    )


def test_without_candidate_genes_the_prompt_has_no_genes_line(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    agent(hpo, iter([answer(("OMIM:690001", "x", "fits"))])).predict(question_of(case))
    assert "Candidate genes" not in str(RECEIVED[0][1].content)

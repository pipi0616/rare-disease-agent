"""The agent, driven by a scripted fake model on the miniature HPO release: no network, no cost.

The fake model plays the agent's moves; the tools, the middleware and the final
answer are real.
"""

import itertools
import json
from collections.abc import Callable, Iterator

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from conftest import OFFERED, RECEIVED, ScriptedModel, answer, call
from raredx.agent import (
    FILLED,
    FILLED_BOTH,
    FUSED,
    LAST_TURN,
    MAX_MODEL_CALLS,
    Agent,
    NoFinalAnswer,
    as_langchain_tool,
    fuse,
    merge,
    system_prompt,
)
from raredx.baselines import llm_direct
from raredx.baselines.rank_then_check import RankThenCheck
from raredx.data.cases import Case
from raredx.evals.systems import Candidate, question_of
from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.find_similar_patients import FindSimilarPatients
from raredx.tools.rank_candidate_genes import RankCandidateGenes
from raredx.tools.rank_diseases import RankDiseases


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
    assert (params["prompt_version"], params["max_model_calls"]) == ("agent-v4", MAX_MODEL_CALLS)


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
    assert system.name == "seeded-agent" and params["prompt_version"] == "seeded-v2"
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
    first = str(RECEIVED[0][1].content)
    assert "Candidate genes from sequencing (at most one is causal): GENEA, GENEE" in first
    assert "none of whose genes is on this list is unlikely" in first


def test_without_candidate_genes_the_prompt_has_no_genes_line(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    agent(hpo, iter([answer(("OMIM:690001", "x", "fits"))])).predict(question_of(case))
    assert "Candidate genes" not in str(RECEIVED[0][1].content)


def test_fusing_puts_first_the_disease_both_rankings_rank_high() -> None:
    def c(disease: str, gene: str | None = None, reason: str | None = None) -> Candidate:
        return Candidate(disease_name=disease, disease_id=disease, gene=gene, reason=reason)

    agent_ranking = [c("OMIM:1", reason="agent 1"), c("OMIM:2", reason="agent 2"), c("OMIM:3")]
    gene_ranking = [c("OMIM:2", gene="GENE2"), c("OMIM:9", gene="GENE9")]
    fused = fuse(agent_ranking, gene_ranking)
    assert [x.disease_id for x in fused] == ["OMIM:2", "OMIM:1", "OMIM:9", "OMIM:3"]
    assert (fused[0].reason, fused[0].gene) == ("agent 2", "GENE2")  # the agent's words, its gene
    assert fused[2].reason == FUSED  # only the gene ranking had it


def test_with_candidate_genes_the_answer_is_fused_with_the_gene_ranking(
    hpo: HPO, case: Case
) -> None:
    moves = iter([answer(("OMIM:690005", "Frequency-test syndrome", "the agent's pick"))])
    system = Agent(
        ScriptedModel(messages=moves), "deepseek-flash", hpo, extra_tools=[RankCandidateGenes(hpo)]
    )
    question = question_of(case).model_copy(update={"candidate_genes": ["GENEA", "GENEE"]})
    answers = system.predict(question)
    # The gene ranking has GENEA's disease first and GENEE's second; the agent named only
    # GENEE's. Ranked by both, GENEE's disease leads; GENEA's enters from the gene ranking.
    assert [c.disease_id for c in answers[:2]] == ["OMIM:690005", "OMIM:690001"]
    assert answers[0].reason == "the agent's pick" and answers[0].gene == "GENEE"
    assert answers[1].reason == FUSED and answers[1].gene == "GENEA"
    assert "reciprocal rank" in system.params()["fusion"]


def test_without_candidate_genes_nothing_is_fused(hpo: HPO, case: Case) -> None:
    moves = iter([answer(("OMIM:690005", "Frequency-test syndrome", "the agent's pick"))])
    system = Agent(
        ScriptedModel(messages=moves), "deepseek-flash", hpo, extra_tools=[RankCandidateGenes(hpo)]
    )
    assert [c.disease_id for c in system.predict(question_of(case))] == ["OMIM:690005"]


# ── the hypothesis agent: the model's own answer first, then the tools' ──


def first_answer(*guesses: tuple[str, str]) -> AIMessage:
    """The hypothesis agent's first move: the bare model's answer, as (name, id) rows."""
    rows = [{"disease_name": name, "disease_id": disease_id} for name, disease_id in guesses]
    return AIMessage(content=json.dumps({"candidates": rows}))


def hypothesis(hpo: HPO, moves: Iterator[AIMessage]) -> Agent:
    return Agent(ScriptedModel(messages=moves), "deepseek-flash", hpo, hypotheses=True)


def test_the_hypothesis_agent_asks_the_bare_question_before_any_tool(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            first_answer(("Hearing-retina syndrome", "OMIM:690002")),
            answer(("OMIM:690002", "Hearing-retina syndrome", "my own")),
        ]
    )
    hypothesis(hpo, moves).predict(question_of(case))
    asked = RECEIVED[0]
    assert [m.content for m in asked] == [
        llm_direct.SYSTEM_PROMPT,
        llm_direct.user_prompt(question_of(case)),
    ]
    system, first = str(RECEIVED[1][0].content), str(RECEIVED[1][1].content)
    assert "Before any tool ran, you answered from your own knowledge alone" in system
    # its own list first, checked; then the tools', which point to a disease already shown
    assert first.index("[H1] OMIM:690002 Hearing-retina syndrome") < first.index("[T1]")
    assert "explains 1 of 2 findings" in first
    assert "= [H1] Hearing-retina syndrome" in first


def test_a_number_hpo_knows_is_kept_under_hpos_name(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            first_answer(("Hearing-ovarian syndrome", "OMIM:690003")),  # 690003: seizures
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits")),
        ]
    )
    hypothesis(hpo, moves).predict(question_of(case))
    first = str(RECEIVED[1][1].content)
    assert "[H1] OMIM:690003 Seizure disorder" in first  # HPO's name, beside the evidence
    assert "you wrote" not in first


def test_a_number_hpo_does_not_know_is_found_by_its_name(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            first_answer(("Hearing ovarian syndrome", "OMIM:999999")),
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits")),
        ]
    )
    hypothesis(hpo, moves).predict(question_of(case))
    first = str(RECEIVED[1][1].content)
    assert "[H1] OMIM:690001 Hearing-ovarian syndrome" in first
    assert "(you wrote Hearing ovarian syndrome (OMIM:999999))" in first


def test_a_name_sharing_only_a_common_word_is_not_taken_for_the_disease(
    hpo: HPO, case: Case
) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            first_answer(("Wolfram syndrome", "OMIM:999999")),  # 86 to Hearing-ovarian syndrome
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits")),
        ]
    )
    hypothesis(hpo, moves).predict(question_of(case))
    first = str(RECEIVED[1][1].content)
    assert "[H1] Wolfram syndrome (OMIM:999999): no disease of this name" in first


def test_a_disease_hpo_does_not_know_is_listed_unchecked(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            first_answer(("Zzyzx qwerty", "OMIM:123456")),
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits")),
        ]
    )
    hypothesis(hpo, moves).predict(question_of(case))
    first = str(RECEIVED[1][1].content)
    assert (
        "[H1] Zzyzx qwerty (OMIM:123456): no disease of this name in the HPO annotations" in first
    )


def test_the_mask_hides_a_guessed_disease_known_only_from_the_masked_paper(
    hpo: HPO, case: Case
) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            first_answer(("Amenorrhea known from one paper", "OMIM:690004")),
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits")),
        ]
    )
    with masking.masked(["PMID:1004"]):
        hypothesis(hpo, moves).predict(question_of(case))
    first = str(RECEIVED[1][1].content)
    assert "no disease of this name in the HPO annotations" in first
    assert "OMIM:690004" not in first.split("[T1]")[0].replace("(OMIM:690004)", "")


def test_an_unreadable_first_answer_is_asked_again_once_then_left_out(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            AIMessage(content="not json"),
            AIMessage(content="still not json"),
            answer(("OMIM:690001", "Hearing-ovarian syndrome", "fits")),
        ]
    )
    answers = hypothesis(hpo, moves).predict(question_of(case))
    assert "not in the required format" in str(RECEIVED[1][-1].content)
    assert "(none: your first answer could not be read)" in str(RECEIVED[2][1].content)
    assert answers[0].disease_id == "OMIM:690001"


def test_a_short_answer_is_filled_from_both_lists_merged(hpo: HPO, case: Case) -> None:
    moves = iter(
        [
            first_answer(
                ("Seizure disorder", "OMIM:690003"), ("Frequency-test syndrome", "OMIM:690005")
            ),
            answer(("OMIM:690004", "Amenorrhea known from one paper", "my pick")),
        ]
    )
    answers = hypothesis(hpo, moves).predict(question_of(case))
    tools_order = [
        m.disease_id
        for m, _ in RankThenCheck(RankDiseases(hpo), CheckMatch(hpo)).ordered(question_of(case))
    ]
    merged = merge(["OMIM:690003", "OMIM:690005"], tools_order)
    assert [c.disease_id for c in answers] == ["OMIM:690004"] + [
        d for d in merged if d != "OMIM:690004"
    ]
    assert answers[0].reason == "my pick"
    assert all(c.reason == FILLED_BOTH for c in answers[1:])


def test_merging_puts_first_what_both_lists_rank_and_then_takes_turns() -> None:
    assert merge(["A", "B", "D"], ["B", "C"]) == ["B", "A", "C", "D"]


def test_the_hypothesis_agent_records_its_first_answer_seed_and_fill(hpo: HPO) -> None:
    system = hypothesis(hpo, iter([]))
    params = system.params()
    assert system.name == "hypothesis-agent" and params["prompt_version"] == "hypotheses-v3"
    assert params["first_answer"].startswith(llm_direct.PROMPT_VERSION)
    assert "reciprocal rank" in params["fill"]


def test_the_text_search_is_named_in_the_hypothesis_prompt_only_when_offered() -> None:
    core = ["rank_diseases", "check_match", "lookup_disease", "find_disease"]
    assert "search_disease_texts" not in system_prompt(core, hypotheses=True)
    with_texts = system_prompt([*core, "search_disease_texts"], hypotheses=True)
    assert "read how it is described with search_disease_texts" in with_texts


def test_given_prevalence_each_disease_shows_how_common_it_is(hpo: HPO, case: Case) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            first_answer(("Hearing-retina syndrome", "OMIM:690002")),
            answer(("OMIM:690002", "Hearing-retina syndrome", "my own")),
        ]
    )
    common = {"OMIM:690002": "1-5 / 10 000"}
    system = Agent(
        ScriptedModel(messages=moves), "deepseek-flash", hpo, hypotheses=True, prevalence=common
    )
    system.predict(question_of(case))
    prompt, first = str(RECEIVED[1][0].content), str(RECEIVED[1][1].content)
    assert "the more common is the likelier" in prompt
    assert "An unknown prevalence is not evidence of rarity" in prompt
    head = next(line for line in first.splitlines() if line.startswith("[H1]"))
    assert head.endswith("· prevalence 1-5 / 10 000 (Orphanet)")
    assert "· prevalence unknown (Orphanet)" in first  # the tools' others, not classed
    assert system.params()["prompt_version"] == "hypotheses-v4"


def test_without_prevalence_neither_the_prompt_nor_the_lists_mention_it(
    hpo: HPO, case: Case
) -> None:
    RECEIVED.clear()
    moves = iter(
        [
            first_answer(("Hearing-retina syndrome", "OMIM:690002")),
            answer(("OMIM:690002", "Hearing-retina syndrome", "my own")),
        ]
    )
    hypothesis(hpo, moves).predict(question_of(case))
    assert "prevalence" not in str(RECEIVED[1][0].content) + str(RECEIVED[1][1].content)

"""B2, the fixed pipeline, on the miniature HPO release with a fake model: no network, no cost."""

import json
from collections.abc import Callable

import pytest

from conftest import FakeLLM
from raredx.baselines.fixed_pipeline import SYSTEM_PROMPT, FixedPipeline, user_prompt
from raredx.data.cases import Case
from raredx.evals.systems import question_of
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.lookup_disease import LookupDisease
from raredx.tools.rank_diseases import RankDiseases


def pipeline(hpo: HPO, client: FakeLLM) -> FixedPipeline:
    return FixedPipeline(
        client,  # type: ignore[arg-type]
        "deepseek-flash",
        RankDiseases(hpo),
        CheckMatch(hpo),
        LookupDisease(hpo),
    )


@pytest.fixture
def case(make_case: Callable[..., Case]) -> Case:
    # Hearing loss and seizures: the tools order OMIM:690005, 690003, 690001, 690002.
    return make_case(
        "1",
        hpo_ids=["HP:0000407", "HP:0001250"],
        hpo_labels=["Sensorineural hearing impairment", "Seizure"],
        sex="FEMALE",
    )


def reply(*ranking: tuple[str, str]) -> str:
    return json.dumps({"ranking": [{"disease_id": d, "reason": r} for d, r in ranking]})


def test_the_model_sees_the_findings_and_each_candidates_evidence(
    hpo: HPO, case: Case, fake_llm: type[FakeLLM]
) -> None:
    client = fake_llm(reply(("OMIM:690005", "explains both")))
    pipeline(hpo, client).predict(question_of(case))
    prompt = client.requests[0]["messages"][-1]["content"]
    assert "Findings (HPO): Sensorineural hearing impairment; Seizure" in prompt
    assert (
        "[1] OMIM:690005 Frequency-test syndrome · genes GENEE · "
        "Autosomal recessive inheritance · Congenital onset"
    ) in prompt
    assert "explains 2 of 2 findings" in prompt
    # OMIM:690003's source looked for hearing impairment in four patients and found none.
    assert "recorded absent in this disease: Sensorineural hearing impairment (0/4)" in prompt
    assert case.pmid not in prompt and "json" in SYSTEM_PROMPT


def test_a_finding_matched_through_the_ontology_says_what_it_matched(
    hpo: HPO, make_case: Callable[..., Case]
) -> None:
    question = question_of(make_case("2", hpo_ids=["HP:0008619"], hpo_labels=["Bilateral SNHL"]))
    report = CheckMatch(hpo)(question.hpo_ids, "OMIM:690001")
    profile = LookupDisease(hpo)("OMIM:690001", max_features=1)
    assert (
        "Bilateral sensorineural hearing impairment (as Sensorineural hearing impairment, 2/2)"
        in (user_prompt(question, [(report, profile)]))
    )


def test_the_models_order_is_kept_with_its_reasons_and_the_rest_follow(
    hpo: HPO, case: Case, fake_llm: type[FakeLLM]
) -> None:
    client = fake_llm(
        reply(
            ("OMIM:690003", "seizures fit"),
            ("OMIM:999999", "not a candidate"),  # dropped: the model may only reorder
            ("690005", "explains both"),  # an id without its prefix is still understood
        )
    )
    answer = pipeline(hpo, client).predict(question_of(case))
    assert [(c.disease_id, c.reason) for c in answer] == [
        ("OMIM:690003", "seizures fit"),
        ("OMIM:690005", "explains both"),
        ("OMIM:690001", None),  # left out by the model: kept in the tools' order
        ("OMIM:690002", None),
    ]


def test_a_reply_naming_no_candidate_is_repaired_once_then_fails(
    hpo: HPO, case: Case, fake_llm: type[FakeLLM]
) -> None:
    client = fake_llm(reply(("OMIM:999999", "x")), reply(("OMIM:888888", "y")))
    with pytest.raises(ValueError, match="none of the candidates"):
        pipeline(hpo, client).predict(question_of(case))
    assert len(client.requests) == 2
    assert "names none of the candidates" in client.requests[1]["messages"][-1]["content"]


def test_the_model_is_asked_for_json_with_reasoning_off(
    hpo: HPO, case: Case, fake_llm: type[FakeLLM]
) -> None:
    client = fake_llm(reply(("OMIM:690005", "explains both")))
    system = pipeline(hpo, client)
    system.predict(question_of(case))
    request = client.requests[0]
    assert request["response_format"] == {"type": "json_object"}
    assert request["extra_body"] == {"thinking": {"type": "disabled"}}
    assert request["temperature"] == 0.0
    assert system.name == "fixed-pipeline"
    assert system.params()["prompt_version"] == "pipeline-v1"
    assert (system.params()["pool"], system.params()["shown"]) == ("30", "10")

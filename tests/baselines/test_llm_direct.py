"""The single-call baseline against a fake client: no network, no cost."""

import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from conftest import FakeLLM
from raredx import llm
from raredx.baselines.llm_direct import SYSTEM_PROMPT, LLMDirect, parse, user_prompt
from raredx.config import Settings
from raredx.data.cases import Case
from raredx.evals.systems import question_of

ANSWER = {
    "candidates": [
        {"disease_name": f"Disease {i}", "disease_id": f"OMIM:6211{i:02d}", "gene": f"G{i}"}
        for i in range(12)
    ]
}


FakeClient = FakeLLM


def system(client: FakeLLM, *, thinking: bool = False) -> LLMDirect:
    return LLMDirect(client, "deepseek-flash", thinking=thinking)  # type: ignore[arg-type]


def test_the_prompt_carries_the_phenotype_and_no_part_of_the_answer(
    make_case: Callable[..., Case],
) -> None:
    case = make_case("1", hpo_ids=["HP:0000786"], hpo_labels=["Primary amenorrhea"], sex="FEMALE")
    text = user_prompt(question_of(case))
    assert "Primary amenorrhea (HP:0000786)" in text and "FEMALE" in text
    assert "Perrault" not in text and "DAP3" not in text and "OMIM" not in text
    assert "json" in SYSTEM_PROMPT  # the provider's JSON mode requires the word


def test_an_answer_is_parsed_and_cut_to_ten() -> None:
    candidates = parse(json.dumps(ANSWER))
    assert len(candidates) == 10
    assert (candidates[0].disease_id, candidates[0].gene) == ("OMIM:621100", "G0")


def test_a_reply_in_the_wrong_format_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse("Perrault syndrome, probably")
    with pytest.raises(ValidationError):
        parse(json.dumps({"diagnoses": []}))


def test_one_repair_attempt_then_the_answer(make_case: Callable[..., Case]) -> None:
    client = FakeClient("not json", json.dumps(ANSWER))
    candidates = system(client).predict(question_of(make_case("1")))
    assert len(candidates) == 10 and len(client.requests) == 2
    repair = client.requests[1]["messages"][-1]["content"]
    assert repair.startswith("That reply was not in the required format")


def test_two_bad_replies_raise_so_the_case_is_scored_as_a_miss(
    make_case: Callable[..., Case],
) -> None:
    client = FakeClient("not json", "still not json")
    with pytest.raises(ValueError):
        system(client).predict(question_of(make_case("1")))


def test_thinking_mode_is_switched_explicitly(make_case: Callable[..., Case]) -> None:
    off, on = FakeClient(json.dumps(ANSWER)), FakeClient(json.dumps(ANSWER))
    system(off).predict(question_of(make_case("1")))
    system(on, thinking=True).predict(question_of(make_case("1")))
    assert off.requests[0]["extra_body"] == {"thinking": {"type": "disabled"}}
    assert off.requests[0]["temperature"] == 0.0
    assert on.requests[0]["extra_body"] == {"thinking": {"type": "enabled"}}
    assert "temperature" not in on.requests[0]
    assert system(on, thinking=True).name == "llm-direct-thinking"


def test_the_api_key_is_read_from_the_providers_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    key = Settings(_env_file=None).llm_api_key  # type: ignore[call-arg]
    assert key is not None and key.get_secret_value() == "sk-test"
    assert "sk-test" not in repr(key)  # SecretStr keeps it out of logs


class BilledClient(FakeLLM):
    """Like FakeLLM, and each reply carries what OpenRouter says the call cost."""

    def __init__(self, *replies: str, cost: float) -> None:
        super().__init__(*replies)
        self.cost = cost
        plain = self.chat.completions.create

        def create(**request: Any) -> Any:
            response = plain(**request)
            response.usage = SimpleNamespace(cost=self.cost, model_extra={})
            return response

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


def test_through_openrouter_reasoning_is_at_its_lowest_and_the_cost_is_asked_for(
    make_case: Callable[..., Case],
) -> None:
    client = BilledClient(json.dumps(ANSWER), cost=0.01)
    budget = llm.Budget(1.0)
    model = LLMDirect(
        client,  # type: ignore[arg-type]
        "anthropic/claude-sonnet-5.5",
        thinking=False,
        provider="openrouter",
        budget=budget,
    )
    assert len(model.predict(question_of(make_case("1")))) == 10
    request = client.requests[0]
    assert request["extra_body"] == {"reasoning": {"effort": "minimal"}, "usage": {"include": True}}
    assert request["temperature"] == 0.0 and request["model"] == "anthropic/claude-sonnet-5.5"
    assert budget.spent == pytest.approx(0.01)
    assert model.name == "llm-direct (anthropic/claude-sonnet-5.5)"
    assert model.params()["provider"] == "openrouter" and model.params()["budget_usd"] == 1.0


def test_the_budget_stops_the_run_before_the_call_that_would_go_over(
    make_case: Callable[..., Case],
) -> None:
    client = BilledClient(json.dumps(ANSWER), json.dumps(ANSWER), cost=0.6)
    model = LLMDirect(
        client,  # type: ignore[arg-type]
        "openai/gpt-6.1-sol",
        thinking=False,
        provider="openrouter",
        budget=llm.Budget(0.5),
    )
    model.predict(question_of(make_case("1")))  # under the cap when it starts
    with pytest.raises(llm.BudgetExceeded, match=r"\$0.6000 spent of a \$0.50 cap"):
        model.predict(question_of(make_case("2")))
    assert len(client.requests) == 1  # the second call was never made


def test_the_openrouter_key_is_read_from_its_own_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.openrouter_api_key is not None
    assert settings.openrouter_api_key.get_secret_value() == "sk-or-test"
    monkeypatch.setenv("OPENROUTER_API_KEY", " ")
    with pytest.raises(llm.MissingAPIKey, match="OPENROUTER_API_KEY"):
        llm.openrouter_client(Settings(_env_file=None))  # type: ignore[call-arg]

"""The single-call baseline against a fake client: no network, no cost."""

import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

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


class FakeClient:
    """Stands in for OpenAI(): returns the replies given, records every request."""

    def __init__(self, *replies: str) -> None:
        self.replies = list(replies)
        self.requests: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **request: Any) -> Any:
        self.requests.append(request)
        message = SimpleNamespace(content=self.replies.pop(0))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def system(client: FakeClient, *, thinking: bool = False) -> LLMDirect:
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

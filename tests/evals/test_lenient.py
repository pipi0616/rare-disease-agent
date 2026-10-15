"""DeepRare's judge: its prompt, how its replies are read, and that judged answers are kept."""

import json
from pathlib import Path
from typing import Any

import pytest

from raredx.evals import lenient


def test_the_question_is_deeprares_word_for_word() -> None:
    eval_py = Path(__file__).resolve().parents[2] / "third_party" / "DeepRare" / "eval.py"
    if eval_py.exists():  # the checkout is local only; the prompt is in it verbatim
        source = eval_py.read_text(encoding="utf-8")
        assert f'system_prompt = "{lenient.SYSTEM}"' in source
        assert "only output the top rank. Output only" in source
    asked = lenient.question(["A", "B", "C", "D", "E", "F"], "B")
    assert asked.startswith(lenient.PROMPT)
    assert "Predicted diseases: 1. A\n2. B\n3. C\n4. D\n5. E\n" in asked and "6. F" not in asked
    assert asked.endswith("Standard diagnosis: B\n")


def test_replies_are_read_as_eval_py_reads_them() -> None:
    assert lenient.parse("No") is None
    assert lenient.parse("2") == 2
    assert lenient.parse("Rank: 3") == 3
    with pytest.raises(ValueError):
        lenient.parse("maybe")
    with pytest.raises(ValueError):
        lenient.parse("7")


def test_judged_answers_are_kept_and_not_asked_again(fake_llm: Any, tmp_path: Path) -> None:
    path = tmp_path / "lenient.json"
    first = fake_llm("1", "No")
    answers = {"c1": {"deeprare": ["X"], "agent": ["Y", "X"]}}
    rows = lenient.judge_all(lenient.Judge(first, "m"), answers, {"c1": "X"}, path)
    assert rows == [{"case_id": "c1", "deeprare": 1, "agent": None}]
    request = first.requests[0]
    assert request["temperature"] == 0.0 and request["messages"][0]["content"] == lenient.SYSTEM
    # asked again with one more case: only the new one costs a call
    again = fake_llm("2")
    answers["c2"] = {"deeprare": ["Z"]}
    rows = lenient.judge_all(lenient.Judge(again, "m"), answers, {"c1": "X", "c2": "Z"}, path)
    assert len(again.requests) == 1 and rows[1] == {"case_id": "c2", "deeprare": 2}
    assert json.loads(path.read_text())[0]["deeprare"] == 1


def test_an_empty_answer_is_no_rank_and_no_call(fake_llm: Any) -> None:
    client = fake_llm()
    assert lenient.Judge(client, "m").rank([], "X") is None and client.requests == []

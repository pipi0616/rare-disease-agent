"""DeepRare's own way of judging an answer: a model reads the five diseases a system
named and the confirmed diagnosis, and says at which rank (1–5) it is named, or "No".

Scoring by OMIM id is the rule everywhere else. DeepRare answers in names, and a
name that matches no OMIM entry closely enough is a miss there, even when it names
the confirmed disease; so its comparisons also report this judge — applied to every
system compared, with the same judge model and prompt. The prompt is DeepRare's
eval.py, word for word; each system's five names are listed the same way.

Judged answers are saved as they come: a run asked again reads them back and pays
only for what is new.
"""

import json
import re
from pathlib import Path

from openai import OpenAI

from raredx.llm import Budget

SYSTEM = "You are a specialist in the field of rare diseases."
# third_party/DeepRare/eval.py, diagnosis_evaluate
PROMPT = (
    "I will now give you five predicted diseases if the predicted diagnosis is in the standard "
    'diagnosis. Please output the predicted rank, otherwise output "No", only output "No" or '
    '"1-5" numbers, if the predicted disease has multiple conditions, only output the top rank. '
    'Output only "No" or one number, no additional output.'
)
TOP = 5


def question(names: list[str], confirmed: str) -> str:
    predicted = "\n".join(f"{i}. {name}" for i, name in enumerate(names[:TOP], 1))
    return f"{PROMPT}Predicted diseases: {predicted}\nStandard diagnosis: {confirmed}\n"


def parse(reply: str) -> int | None:
    """The judge's reply as a rank, as eval.py reads it: "No" is no rank; otherwise the
    first number 1–5. Anything else is an error, not a guess."""
    if "No" in reply or "否" in reply:
        return None
    found = re.findall(r"\b(?:10|[1-9])\b", reply)
    if not found or int(found[0]) > TOP:
        raise ValueError(f"the judge replied {reply!r}")
    return int(found[0])


class Judge:
    def __init__(self, client: OpenAI, model: str, budget: Budget | None = None) -> None:
        self.client = client
        self.model = model
        self.budget = budget

    def rank(self, names: list[str], confirmed: str) -> int | None:
        if not names:
            return None  # nothing named: nothing to judge, and nothing to pay for
        if self.budget is not None:
            self.budget.check()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": question(names, confirmed)},
            ],
            temperature=0.0,
            extra_body={"thinking": {"type": "disabled"}},
        )
        if self.budget is not None:
            self.budget.charge(response)
        return parse(response.choices[0].message.content or "")


def judge_all(
    judge: Judge,
    answers: dict[str, dict[str, list[str]]],
    confirmed: dict[str, str],
    path: Path,
) -> list[dict[str, int | None | str]]:
    """Each case's rank under each system ({case: {system: five names}}), saved to
    `path` after every case; cases already there are read back, not asked again."""
    done: dict[str, dict[str, int | None | str]] = {}
    if path.exists():
        done = {row["case_id"]: row for row in json.loads(path.read_text())}
    for case_id, by_system in answers.items():
        row = done.setdefault(case_id, {"case_id": case_id})
        for system, names in by_system.items():
            if system not in row:
                row[system] = judge.rank(names, confirmed[case_id])
        path.write_text(json.dumps(list(done.values()), indent=1, ensure_ascii=False) + "\n")
    return [done[case_id] for case_id in answers]

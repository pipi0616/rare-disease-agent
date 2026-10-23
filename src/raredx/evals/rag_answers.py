"""Does the model answer better with the texts? The second layer of chapter 33's RAG
evaluation (the first, retrieval, is raredx.evals.rag).

The same questions on how a disease is inherited, asked of the model twice:

- closed book: from what it knows;
- open book (RAG): from the five passages the tool returns for that disease (filtered
  to it, the case's paper masked), told to say "not stated" when they do not, and to
  name the passages it answered from.

Scored by code, not by a second model: the answer is one of a few categories,
checked against Orphanet's; an open-book answer is grounded when a passage it names
says it, by the same wording test retrieval is scored with. A free-text answer would
need a model as judge (MLflow has some built in); a category does not, and code
cannot be talked round.
"""

import json
import random
import re
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from raredx.evals import rag
from raredx.knowledge.text_index import TextIndex
from raredx.knowledge.texts import Passage
from raredx.llm import Budget, Tally, ask_json

PROMPT_VERSION = "rag-answers-v1"
SEED = 20261023
NOT_STATED = "not stated"
# Orphanet's types, as categories a model can answer with; the wording a passage
# would use for each is the retrieval test's.
CATEGORY = {
    "Autosomal recessive": "autosomal recessive",
    "Autosomal dominant": "autosomal dominant",
    "X-linked recessive": "X-linked",
    "X-linked dominant": "X-linked",
    "Mitochondrial inheritance": "mitochondrial",
    "Multigenic/multifactorial": "multifactorial",
    "Semi-dominant": "other",
    "Y-linked": "other",
    "Oligogenic": "other",
}
CATEGORIES = sorted(set(CATEGORY.values())) + [NOT_STATED]
WORDING = {CATEGORY[t]: pattern for t, pattern in rag.INHERITANCE.items()}
SYSTEM = "You answer questions about rare diseases. Reply with a json object."


class Answer(BaseModel):
    inheritance: str
    passages: list[int] = []


class Result(BaseModel):
    source: str
    case_id: str
    disease: str
    truth: list[str]  # Orphanet's, as categories
    retrieved_says: bool  # a returned passage says the truth
    closed: str
    open: str
    cited: list[int]
    grounded: bool  # a passage the open answer names says that answer


def truth(question: rag.Question) -> list[str]:
    """The question's answer, as categories (its patterns are the categories' wording)."""
    return sorted({c for c, pattern in WORDING.items() if pattern in question.answer})


def _shown(passage: Passage) -> str:
    """What the model is shown of a passage: its larger chunk, if it is a small piece."""
    return passage.parent or passage.text


def _parse(content: str | None) -> Answer:
    answer = Answer.model_validate(json.loads(content or ""))
    if answer.inheritance not in CATEGORIES:
        raise ValueError(f"inheritance must be one of {', '.join(CATEGORIES)}")
    return answer


def closed_book(name: str) -> list[ChatCompletionMessageParam]:
    return [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": f"How is {name} inherited? Choose one of: {', '.join(CATEGORIES)} "
            f'("{NOT_STATED}" if you do not know). Reply as {{"inheritance": "..."}}.',
        },
    ]


def open_book(name: str, passages: Sequence[Passage]) -> list[ChatCompletionMessageParam]:
    numbered = "\n\n".join(f"[{i}] {_shown(p)}" for i, p in enumerate(passages, 1))
    return [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": f"Passages:\n\n{numbered}\n\nFrom these passages only: how is {name} "
            f"inherited? Choose one of: {', '.join(CATEGORIES)} "
            f'("{NOT_STATED}" if the passages do not say). Reply as '
            '{"inheritance": "...", "passages": [the numbers of the passages that say it]}.',
        },
    ]


def sample(questions: list[rag.Question], n: int) -> list[rag.Question]:
    """n inheritance questions drawn with a fixed seed (all of them when fewer)."""
    asked = [q for q in questions if q.kind == "inheritance"]
    random.Random(SEED).shuffle(asked)
    return sorted(asked[:n], key=lambda q: (q.source, q.case_id))


def run(
    index: TextIndex[Passage],
    questions: list[rag.Question],
    api: OpenAI,
    model: str,
    budget: Budget,
    tally: Tally,
    workers: int = 8,
) -> list[Result]:
    def one(q: rag.Question) -> Result:
        name = q.text.rsplit(":", 1)[0]
        passages = rag.ask(index, q, rag.Config(filtered=True), None)
        known = truth(q)
        says = any(any(re.search(WORDING[c], _shown(p).lower()) for c in known) for p in passages)
        closed = ask_json(api, model, closed_book(name), _parse, budget=budget, tally=tally)
        opened = ask_json(api, model, open_book(name, passages), _parse, budget=budget, tally=tally)
        cited = [i for i in opened.passages if 1 <= i <= len(passages)]
        wording = WORDING.get(opened.inheritance)
        grounded = wording is not None and any(
            re.search(wording, _shown(passages[i - 1]).lower()) for i in cited
        )
        return Result(
            source=q.source,
            case_id=q.case_id,
            disease=q.disease,
            truth=known,
            retrieved_says=says,
            closed=closed.inheritance,
            open=opened.inheritance,
            cited=cited,
            grounded=grounded,
        )

    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(one, questions))


def summary(results: list[Result]) -> dict[str, Any]:
    """Per book: right, wrong (a category Orphanet does not give), not stated; for the
    open book also grounded answers, and how often the passages held the truth."""
    n = len(results)

    def shares(answers: list[str]) -> dict[str, float]:
        right = sum(a in r.truth for a, r in zip(answers, results, strict=True))
        silent = sum(a == NOT_STATED for a in answers)
        return {"right": right / n, "wrong": (n - right - silent) / n, "not_stated": silent / n}

    answered = [r for r in results if r.open != NOT_STATED]
    return {
        "n": n,
        "closed": shares([r.closed for r in results]),
        "open": shares([r.open for r in results])
        | {"grounded": sum(r.grounded for r in answered) / max(1, len(answered))},
        "passages_say_it": sum(r.retrieved_says for r in results) / n,
        "open_right_when_passages_say_it": sum(
            r.open in r.truth for r in results if r.retrieved_says
        )
        / max(1, sum(r.retrieved_says for r in results)),
    }

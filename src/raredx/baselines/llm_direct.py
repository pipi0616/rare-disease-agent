"""Baseline: ask the model once. No tools, no retrieval — the phenotype in, ten diagnoses out.

This is the single-call control from the plan. It measures what the model
knows on its own, and the agent has to beat it to justify its tools. One
caveat travels with the number: these patients come from published case
reports the model may have read during training, so a correct answer can be
recall rather than reasoning. The score is an upper bound on what the model
can do unaided; a held-out set published after its training cutoff will test
how much of it is memory.

The prompt lives here, in code, so a change to it is reviewed like any other
change; PROMPT_VERSION is recorded with every run.
"""

import json
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ValidationError

from raredx.evals.systems import Candidate, Question

PROMPT_VERSION = "direct-v1"
MAX_CANDIDATES = 10

SYSTEM_PROMPT = """\
You are a clinical geneticist. You will be given the phenotype of a patient with a \
suspected rare Mendelian disease, as Human Phenotype Ontology (HPO) terms.

List the 10 most likely diagnoses, most likely first. For each, give:
- disease_name: the name of the disease
- disease_id: its OMIM phenotype number, written OMIM:nnnnnn (six digits)
- gene: the HGNC symbol of the causal gene

Answer with a json object only, in exactly this format:
{"candidates": [{"disease_name": "...", "disease_id": "OMIM:123456", "gene": "ABC1"}]}"""


def user_prompt(question: Question) -> str:
    lines = [f"Sex: {question.sex or 'unknown'}", "Phenotype (HPO):"]
    lines += [
        f"- {label} ({term})"
        for label, term in zip(question.hpo_labels, question.hpo_ids, strict=True)
    ]
    return "\n".join(lines)


class ModelAnswer(BaseModel):
    candidates: list[Candidate]


def parse(content: str | None) -> list[Candidate]:
    """The model's reply as ranked candidates; raises if it is not the required format."""
    answer = ModelAnswer.model_validate(json.loads(content or ""))
    return answer.candidates[:MAX_CANDIDATES]


class LLMDirect:
    """One chat-completions call per patient, with one repair attempt if the format is wrong."""

    def __init__(self, client: OpenAI, model: str, *, thinking: bool) -> None:
        self.client = client
        self.model = model
        self.thinking = thinking
        self.name = "llm-direct-thinking" if thinking else "llm-direct"

    def params(self) -> dict[str, Any]:
        return {"model": self.model, "thinking": self.thinking, "prompt_version": PROMPT_VERSION}

    def _ask(self, messages: list[ChatCompletionMessageParam]) -> str | None:
        options: dict[str, Any] = {
            "response_format": {"type": "json_object"},
            "extra_body": {"thinking": {"type": "enabled" if self.thinking else "disabled"}},
        }
        if not self.thinking:  # temperature has no effect in thinking mode
            options["temperature"] = 0.0
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, **options
        )
        content: str | None = response.choices[0].message.content
        return content

    def predict(self, question: Question) -> list[Candidate]:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt(question)},
        ]
        content = self._ask(messages)
        try:
            return parse(content)
        except (ValueError, ValidationError) as first_error:
            # One repair attempt: show the model what was wrong. A second failure is
            # raised, recorded in the trace and scored as a miss.
            messages += [
                {"role": "assistant", "content": content or ""},
                {
                    "role": "user",
                    "content": f"That reply was not in the required format ({first_error}). "
                    "Reply again with only the json object.",
                },
            ]
            return parse(self._ask(messages))

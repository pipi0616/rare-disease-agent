"""The judge: decide the diagnosis from an agent's recorded evidence, in one model call.

Chapter 20's error analysis found the agent's bottleneck in its final judgment,
not in finding: in 46 dev cases it had examined the right disease and ranked
another first, often a close relative, weighing the tools' evidence one way in
one case and the other way in the next.

Trying a new way of judging by rerunning the whole agent costs a full run per
idea. Instead, the evidence the agent gathered is read back from its trace
(evals/evidence.py) and laid out as one row per candidate, and a judge decides
on it in one call per case — about a tenth of a run. A variant that wins here,
paired against the agent's own answers, is then built into the agent.

Variants (prompt versions are recorded with each run):

- table: the evidence table alone, with explicit rules for weighing it;
- review: the same table and the agent's own ranking and reasons, to be
  checked against the evidence and corrected where it disagrees;
- either, with the model's thinking mode on.

The judge ranks only candidates in the table. Its list is filled to ten with
the agent's own answers, in the agent's order, so top-10 stays comparable.
"""

from typing import Any

import mlflow
from mlflow.entities import SpanType
from openai import OpenAI

from raredx import llm
from raredx.baselines.fixed_pipeline import parse
from raredx.evals.evidence import CandidateEvidence, CaseEvidence
from raredx.evals.systems import Candidate, Question

VARIANTS = ("table", "review")
PROMPT_VERSIONS = {"table": "judge-table-v1", "review": "judge-review-v1"}

_WEIGHING = """\
Weigh the evidence the same way for every candidate:
1. Findings explained, above all the rare and specific ones. Findings its patients were \
checked for and lacked (recorded absent), and frequent features the patient lacks, count \
against it.
2. Similar published patients are independent evidence: real patients whose findings \
resemble this patient's and whose diagnosis was confirmed. When several of the most \
similar patients, from different papers, share a diagnosis, it can outweigh a disease \
whose pooled annotation explains a finding or two more — annotations are incomplete, \
patients are not averages.
3. Inheritance and onset should fit the patient.
4. Between close candidates (subtypes of one disease family), decide on the findings \
that tell them apart, not on the ones they share."""

TABLE_PROMPT = f"""\
You are a clinical geneticist. You will be given the findings of a patient with a \
suspected rare Mendelian disease and an evidence table for candidate diseases, gathered \
by tools: where the phenotype ranking put each, which of the patient's findings it \
explains and how often its patients show them, which it does not, findings its patients \
were found to lack, its frequent features the patient lacks, how many of the most \
similar published patients had it, and its genes, inheritance and onset.

{_WEIGHING}

Rank up to 10 of the candidates given, most likely first, each once, each with one \
sentence of reason. Answer with a json object only, in exactly this format:
{{"ranking": [{{"disease_id": "OMIM:123456", "reason": "one sentence"}}]}}"""

REVIEW_PROMPT = f"""\
You are a clinical geneticist reviewing a colleague's differential diagnosis. You will \
be given the findings of a patient with a suspected rare Mendelian disease, an evidence \
table for candidate diseases gathered by tools, and your colleague's ranking with a \
reason for each. Check the ranking against the evidence and correct it where the \
evidence disagrees; keep it where it holds.

{_WEIGHING}

Give your final ranking: up to 10 of the candidates given, most likely first, each \
once, each with one sentence of reason. Answer with a json object only, in exactly this \
format:
{{"ranking": [{{"disease_id": "OMIM:123456", "reason": "one sentence"}}]}}"""


def _row(i: int, c: CandidateEvidence) -> list[str]:
    facts = [f"genes {', '.join(c.genes) or 'unknown'}", *c.inheritance, *c.onset_and_course]
    lines = [f"[{i}] {c.disease_id} {c.disease_name} · " + " · ".join(facts)]
    if c.phenotype_rank:
        lines.append(f"    phenotype ranking: #{c.phenotype_rank}")
    if c.n_findings is not None:
        lines.append(
            f"    explains {len(c.explained)} of {c.n_findings} findings: "
            + ("; ".join(c.explained) or "none")
        )
        if c.unexplained:
            lines.append("    not explained: " + "; ".join(c.unexplained))
        if c.contradicted:
            lines.append("    recorded absent in its patients: " + "; ".join(c.contradicted))
        if c.missing:
            lines.append("    frequent in it, not in the patient: " + "; ".join(c.missing))
    else:
        lines.append("    not checked against the patient")
    if c.patients_retrieved:
        lines.append(
            f"    similar published patients: {c.similar_patients} of the "
            f"{c.patients_retrieved} most similar"
            + (f", from {c.similar_papers} paper(s)" if c.similar_patients else "")
        )
    if c.text_sources:
        lines.append("    described in: " + "; ".join(c.text_sources[:3]))
    return lines


def table(evidence: CaseEvidence) -> str:
    lines = ["Candidates (in no particular order of likelihood):"]
    for i, c in enumerate(evidence.candidates, 1):
        lines += _row(i, c)
    return "\n".join(lines)


def colleague(evidence: CaseEvidence) -> str:
    ranked = sorted(
        (c for c in evidence.candidates if c.agent_rank), key=lambda c: c.agent_rank or 0
    )
    lines = ["Your colleague's ranking:"]
    lines += [f"{c.agent_rank}. {c.disease_id} {c.disease_name}: {c.agent_reason}" for c in ranked]
    return "\n".join(lines)


def user_prompt(question: Question, evidence: CaseEvidence, variant: str) -> str:
    parts = [
        f"Sex: {question.sex or 'unknown'}\nFindings (HPO): " + "; ".join(question.hpo_labels),
        table(evidence),
    ]
    if variant == "review":
        parts.append(colleague(evidence))
    return "\n\n".join(parts)


class EvidenceJudge:
    def __init__(
        self,
        client: OpenAI,
        model: str,
        evidence: dict[str, CaseEvidence],
        agent_answers: dict[str, list[Candidate]],
        source_run: str,
        variant: str = "table",
        *,
        thinking: bool = False,
    ) -> None:
        if variant not in VARIANTS:
            raise ValueError(f"unknown judge {variant!r}: choose {', '.join(VARIANTS)}")
        self.client = client
        self.model = model
        self.evidence = evidence
        self.agent_answers = agent_answers
        self.source_run = source_run
        self.variant = variant
        self.thinking = thinking
        self.name = f"judge-{variant}" + ("-thinking" if thinking else "")

    def params(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "thinking": self.thinking,
            "prompt_version": PROMPT_VERSIONS[self.variant],
            "source_run": self.source_run,
            "replay": "the source run's recorded evidence, one model call per case",
        }

    @mlflow.trace(name="recorded_evidence", span_type=SpanType.TOOL)
    def recorded(self, case_id: str) -> CaseEvidence:
        """The evidence the agent gathered for the case: what the judge reads, recorded
        as a tool output so the leak audit reads it too."""
        return self.evidence[case_id]

    def predict(self, question: Question) -> list[Candidate]:
        evidence = self.recorded(question.case_id)
        names = {c.disease_id: c for c in evidence.candidates}
        system = REVIEW_PROMPT if self.variant == "review" else TABLE_PROMPT
        ranking = llm.ask_json(
            self.client,
            self.model,
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt(question, evidence, self.variant)},
            ],
            lambda content: parse(content, list(names)),
            thinking=self.thinking,
        )
        answers = [
            Candidate(
                disease_name=names[d].disease_name,
                disease_id=d,
                gene=names[d].genes[0] if len(names[d].genes) == 1 else None,
                reason=reason,
            )
            for d, reason in ranking[:10]
        ]
        for c in self.agent_answers.get(question.case_id, []):  # fill to ten, as the agent did
            if len(answers) >= 10:
                break
            if all(a.disease_id != c.disease_id for a in answers):
                answers.append(c)
        return answers

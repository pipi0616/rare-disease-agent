"""B2 · the fixed pipeline: the tools look things up in a fixed order, then the model judges.

1. rank_diseases proposes 30 candidates and check_match reorders them
   (rank-then-check);
2. the top 10 are looked up (lookup_disease: genes, inheritance, onset), and
   their match reports kept (check_match: findings explained, unexplained,
   recorded absent, frequent features the patient lacks);
3. one model call ranks those 10 on that evidence, with a reason for each.

The order of the steps is fixed in code: the model decides nothing about what
is looked up. That is the difference from the agent, which chooses its own
next step, and why this pipeline is the control the agent is compared with.

The model only reorders the tools' candidates. A disease the tools did not
propose cannot enter; a candidate the model leaves out keeps its place after
the ones it ranked. The prompt lives here and is versioned like the single-call
baseline's.
"""

import json
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from raredx import llm
from raredx.baselines.phenotype_rank import candidate
from raredx.baselines.rank_then_check import RankThenCheck
from raredx.evals.scoring import normalize_omim
from raredx.evals.systems import Candidate, Question
from raredx.tools.check_match import CheckMatch, MatchReport
from raredx.tools.lookup_disease import DiseaseProfile, LookupDisease
from raredx.tools.rank_diseases import RankDiseases

PROMPT_VERSION = "pipeline-v1"
SHOWN = 10

SYSTEM_PROMPT = """\
You are a clinical geneticist. You will be given the phenotype of a patient with a \
suspected rare Mendelian disease, and up to 10 candidate diseases proposed by \
phenotype-matching tools. Each candidate comes with evidence from the Human Phenotype \
Ontology (HPO) annotations: which of the patient's findings the disease explains and \
how often its patients show them, which findings it does not explain, findings its \
literature recorded as absent in its patients, and its frequent features the patient \
does not have, with its genes, inheritance and onset.

Rank the candidates by how likely each is to be this patient's diagnosis. Weigh the \
whole picture: a diagnosis should explain the patient's findings, above all the rarer \
and more specific ones; findings recorded as absent and missing hallmark features \
count against it; inheritance and onset should fit the patient. Rank only the \
candidates given, each once.

Answer with a json object only, in exactly this format:
{"ranking": [{"disease_id": "OMIM:123456", "reason": "one sentence"}]}"""


def _evidence(report: MatchReport, profile: DiseaseProfile) -> list[str]:
    facts = [f"genes {', '.join(profile.genes) or 'unknown'}"]
    facts += profile.inheritance + profile.onset_and_course
    explained = [
        f"{e.finding.label} ({e.frequency or 'frequency unknown'})"
        if e.relation == "same"
        else f"{e.finding.label} (as {e.feature}, {e.frequency or 'frequency unknown'})"
        for e in report.explained
    ]
    lines = [
        f"{report.disease_id} {report.disease_name} · " + " · ".join(facts),
        f"    explains {len(report.explained)} of {report.n_findings} findings: "
        + ("; ".join(explained) or "none"),
    ]
    if report.unexplained:
        lines.append("    not explained: " + "; ".join(f.label for f in report.unexplained))
    if report.contradicted:
        absent = [f"{c.finding.label} ({c.frequency})" for c in report.contradicted]
        lines.append("    recorded absent in this disease: " + "; ".join(absent))
    if report.missing:
        missing = [f"{m.feature.label} ({m.frequency})" for m in report.missing]
        lines.append("    frequent in this disease, not in the patient: " + "; ".join(missing))
    return lines


def candidates_block(shown: list[tuple[MatchReport, DiseaseProfile]]) -> str:
    """The tools' candidates, numbered in their order, each with its evidence."""
    lines = ["Candidates, in the order the phenotype tools rank them:"]
    for i, (report, profile) in enumerate(shown, 1):
        first, *rest = _evidence(report, profile)
        lines += [f"[{i}] {first}", *rest]
    return "\n".join(lines)


def user_prompt(question: Question, shown: list[tuple[MatchReport, DiseaseProfile]]) -> str:
    findings = [
        f"Sex: {question.sex or 'unknown'}",
        "Findings (HPO): " + "; ".join(question.hpo_labels),
    ]
    return "\n".join(findings) + "\n\n" + candidates_block(shown)


class Ranked(BaseModel):
    disease_id: str
    reason: str


class ModelRanking(BaseModel):
    ranking: list[Ranked]


def parse(content: str | None, candidate_ids: list[str]) -> list[tuple[str, str]]:
    """The model's order over the candidates, with its reasons. Ids it was not given
    are dropped; a reply naming none of the candidates is rejected."""
    ranking = ModelRanking.model_validate(json.loads(content or "")).ranking
    ordered: dict[str, str] = {}
    for item in ranking:
        disease_id = normalize_omim(item.disease_id)
        if disease_id is not None and disease_id in candidate_ids and disease_id not in ordered:
            ordered[disease_id] = item.reason
    if not ordered:
        raise ValueError("the ranking names none of the candidates given")
    return list(ordered.items())


class FixedPipeline:
    name = "fixed-pipeline"

    def __init__(
        self,
        client: OpenAI,
        model: str,
        rank: RankDiseases,
        check: CheckMatch,
        lookup: LookupDisease,
        *,
        shown: int = SHOWN,
    ) -> None:
        self.client = client
        self.model = model
        self.tools = RankThenCheck(rank, check)
        self.lookup = lookup
        self.shown = shown

    def params(self) -> dict[str, Any]:
        return {
            **self.tools.params(),
            "model": self.model,
            "thinking": False,
            "prompt_version": PROMPT_VERSION,
            "shown": str(self.shown),
        }

    def predict(self, question: Question) -> list[Candidate]:
        top = self.tools.ordered(question)[: self.shown]
        profiles = [self.lookup(match.disease_id, max_features=1) for match, _ in top]
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_prompt(
                    question, [(r, p) for (_, r), p in zip(top, profiles, strict=True)]
                ),
            },
        ]
        ids = [match.disease_id for match, _ in top]
        ranking = llm.ask_json(self.client, self.model, messages, lambda c: parse(c, ids))
        reasons = dict(ranking)
        by_id = {match.disease_id: match for match, _ in top}
        order = [d for d, _ in ranking] + [d for d in ids if d not in reasons]
        return [candidate(by_id[d]).model_copy(update={"reason": reasons.get(d)}) for d in order]

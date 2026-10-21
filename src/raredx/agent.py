"""The agent: the model decides what to look up, and when it has enough.

The same tools as the fixed pipeline, plus find_disease, and no fixed order.
The model calls tools in a loop — LangChain's create_agent, built on LangGraph —
until it gives its final answer: up to ten OMIM diseases, best first, each with
a reason. Unlike the fixed pipeline it can check a disease the ranking did not
propose: one it thinks of, found by name.

Bounds, all LangChain middleware:
- at most MAX_MODEL_CALLS model calls per case. On the last one the model is
  offered only the final answer and told its budget is spent (a wrap_model_call
  middleware of ours): the first runs investigated until they ran out, and a
  model offered one tool may still call the others it saw earlier.
  ModelCallLimitMiddleware stops a model that still does not answer; the case
  then fails, and scores as a miss;
- an error the model can fix — an unknown disease id, arguments that break a
  tool's schema — comes back to it as a message, so it can retry
  (ToolErrorMiddleware); anything else fails the case;
- the final answer is a schema the model must fill (ToolStrategy).

The seeded agent (`seeded=True`) starts where the fixed pipeline stops: its
first message already holds the tools' top ten with their evidence, so its
turns go to what the tools cannot do — a disease they missed, found by name and
checked. A list shorter than ten is filled from the tools' order; those entries
say so in their reason.

The hypothesis agent (`hypotheses=True`) asks the model first, before any tool
ran: the single-call baseline's question, answered from what it knows. Each
disease it names is found in the HPO annotations — by the number it wrote, or
by name when HPO has no such number — and checked as the tools' candidates are.
Its first message holds both lists, the model's own first. Built after v1.0
lost to the bare model on RareBench: seeded with the tools' list alone, it kept
their first candidate where the model knew better. A short list is filled from
both lists, merged by reciprocal rank.

With candidate genes from sequencing, the agent's ranking is fused with the
candidate-gene ranking by reciprocal rank (`fuse`): on dev-200 the two were
right on different cases, and together beat either alone (chapter 20).

The tools run in this process, so the evaluation's mask reaches them exactly as
it reaches the fixed pipeline's. The prompts are versioned like the baselines'.
"""

import functools
import inspect
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ModelRequest,
    ModelResponse,
    ToolErrorMiddleware,
    wrap_model_call,
)
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field, ValidationError

from raredx.baselines import llm_direct
from raredx.baselines.fixed_pipeline import SHOWN, candidates_block, evidence
from raredx.baselines.gene_rank import GeneRank
from raredx.baselines.llm_direct import user_prompt
from raredx.baselines.phenotype_rank import candidate
from raredx.baselines.rank_then_check import RankThenCheck
from raredx.evals.scoring import normalize_omim
from raredx.evals.systems import Candidate, Question
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch, MatchReport
from raredx.tools.find_disease import NAME_MATCH, FindDisease, resolve
from raredx.tools.ids import UnknownDisease
from raredx.tools.lookup_disease import LookupDisease
from raredx.tools.rank_diseases import RankDiseases

PROMPT_VERSION = "agent-v3"
SEEDED_PROMPT_VERSION = "seeded-v1"
HYPOTHESES_PROMPT_VERSION = "hypotheses-v1"
HYPOTHESES_PREVALENCE_PROMPT_VERSION = "hypotheses-v2"  # v1, and how common each disease is
MAX_MODEL_CALLS = 8

_ROLE = """\
You are a clinical geneticist. Your task is to diagnose a patient with a suspected \
rare Mendelian disease from their phenotype, given as Human Phenotype Ontology (HPO) \
terms.

Your tools work over the HPO disease annotations:"""

# One line per tool in the system prompt, in the order the tools are given. A run
# without a tool (an ablation) does not mention it; with the four core tools only, the
# prompt is exactly the one agent-v3 and seeded-v1 were measured with.
GUIDES = {
    "rank_diseases": "every OMIM disease ranked by how well its phenotype matches. Start here.",
    "check_match": "the patient's findings against one disease: which it explains, which "
    "it does not, which its patients were found not to have, and its frequent features "
    "the patient lacks.",
    "lookup_disease": "one disease's features and their frequencies, inheritance, onset, genes.",
    "find_disease": "the OMIM id of a disease you have in mind, by name.",
    "find_similar_patients": "published patients whose phenotype resembles this one, with "
    "their confirmed diagnoses (from Phenopacket Store, not the HPO annotations). Call it "
    "beside rank_diseases: a disease several similar patients share is a strong candidate, "
    "even one the ranking missed.",
    "rank_candidate_genes": "the patient's candidate genes from sequencing, ranked by how "
    "well the diseases each is known to cause match the phenotype. Use it first when the "
    "patient has candidate genes: a disease of a well-ranked gene is a strong candidate. A "
    "gene with no known disease may still be causal, but cannot be scored.",
    "search_disease_texts": "search what Orphanet and MedlinePlus write about diseases, in "
    "your own words: key findings, or a disease's name. Use it to read how a candidate is "
    "described, or to find diseases described with findings the other tools weigh poorly; "
    "cite the source.",
}


def _role_and_tools(tools: list[str]) -> str:
    return "\n".join([_ROLE, *(f"- {name}: {GUIDES[name]}" for name in tools)])


_WEIGHING = """\
Weigh the evidence: a diagnosis should \
explain the patient's findings, above all the specific ones; findings recorded absent \
and missing hallmark features count against it; inheritance and onset should fit. You \
may name a disease the tools know little about if you have good reason."""

_INVESTIGATE = f"""

Investigate before you answer. Check the leading candidates with check_match. The \
ranking can miss a disease with few annotations: if you suspect one it did not \
propose, find it by name and check it too. {_WEIGHING}

Your budget is {MAX_MODEL_CALLS} turns, and the last one is for your answer. A few \
rounds are usually enough: rank, check the leading candidates (several calls at \
once), check any you suspect, then answer. When you have enough, give your final \
answer: up to 10 OMIM diseases, most likely first, each with a one-sentence reason."""

_INVESTIGATE_SEEDED = f"""

The tools have already ranked every disease against the patient and checked the \
leading candidates: their evidence is in the first message. Spend your turns on what \
they cannot do: a disease they may have missed (one you suspect, found by name and \
checked), and a closer look where candidates are close. {_WEIGHING}

Your budget is {MAX_MODEL_CALLS} turns, and the last one is for your answer; answer \
sooner if the evidence is clear. Give your final answer: up to 10 OMIM diseases, most \
likely first, each with a one-sentence reason."""


_HOW_COMMON = """ Each disease shows how common Orphanet says it is. Where diseases \
fit comparably, the more common is the likelier: a well-known disease that fits is more \
likely than a far rarer one that explains a few more annotated findings, and a disease \
known from a handful of families needs findings that set it apart. An unknown \
prevalence is not evidence of rarity."""


def _investigate_hypotheses(tools: list[str], prevalence: bool) -> str:
    read = (
        "; read how it is described with search_disease_texts"
        if "search_disease_texts" in tools
        else ""
    )
    common = _HOW_COMMON if prevalence else ""
    return f"""

Before any tool ran, you answered from your own knowledge alone. The first message \
shows that differential ([H1], [H2], ...), each disease found in the HPO annotations \
and checked against the patient, then the phenotype tools' leading candidates \
([T1], [T2], ...), checked the same way. Weigh the two lists as equals: what you know \
of a disease is evidence, as the tools' match is. The HPO annotations are incomplete: \
well-known diseases, above all immune, inflammatory and metabolic ones, can have few \
annotated features, so a disease you suspect for good reason is not ruled out because \
it explains few findings here{read}. Nor is a candidate right because the tools rank \
it first: one that explains only a small part of the patient's findings, none of them \
specific, needs another reason.{common} Spend your turns where the lists disagree, \
or on a disease neither has. {_WEIGHING}

Your budget is {MAX_MODEL_CALLS} turns, and the last one is for your answer; answer \
sooner if the evidence is clear. Give your final answer: up to 10 OMIM diseases, most \
likely first, each with a one-sentence reason."""


def system_prompt(
    tools: list[str], *, seeded: bool = False, hypotheses: bool = False, prevalence: bool = False
) -> str:
    """The system prompt for an agent with these tools."""
    if hypotheses:
        return _role_and_tools(tools) + _investigate_hypotheses(tools, prevalence)
    return f"{_role_and_tools(tools)}{_INVESTIGATE_SEEDED if seeded else _INVESTIGATE}"


FILLED = "Not ranked by the agent: filled in from the phenotype tools' order."
FILLED_BOTH = "Not ranked by the agent: filled in from its first answer and the tools' order."
H_TITLE = (
    "Your own differential, before any tool ran; each disease found in the HPO "
    "annotations and checked against the patient:"
)
T_TITLE = "Candidates, in the order the phenotype tools rank them, checked the same way:"
FUSED = "Not ranked by the agent: a candidate gene's disease, from the gene ranking."
RRF_K = 60  # the usual constant of reciprocal-rank fusion; not tuned


LAST_TURN = (
    "Your budget is spent: this is your last turn. Give your final answer now, with the "
    "FinalAnswer tool, from the evidence you have."
)


def fuse(agent: list[Candidate], genes: list[Candidate]) -> list[Candidate]:
    """The agent's ranking and the candidate-gene ranking as one, by reciprocal rank:
    a disease both rank high comes first. An entry keeps the agent's reason and the
    gene ranking's gene; a disease only the gene ranking has says so in its reason."""
    score: dict[str, float] = defaultdict(float)
    for ranking in (agent, genes):
        for rank, c in enumerate(ranking):
            if c.disease_id:
                score[c.disease_id] += 1 / (RRF_K + rank)
    by_agent = {c.disease_id: c for c in agent}
    by_genes = {c.disease_id: c for c in genes}
    fused = []
    for disease_id in sorted(score, key=lambda d: (-score[d], d))[:10]:
        ranked, gene = by_agent.get(disease_id), by_genes.get(disease_id)
        if ranked is None:
            assert gene is not None
            fused.append(gene.model_copy(update={"reason": FUSED}))
        elif gene is not None:
            fused.append(ranked.model_copy(update={"gene": gene.gene or ranked.gene}))
        else:
            fused.append(ranked)
    return fused


def merge(first: list[str], tools: list[str]) -> list[str]:
    """Two rankings of disease ids as one, by reciprocal rank: a disease both rank high
    comes first. Ties go in turn, the first ranking's first (H1, T1, H2, T2, ...)."""
    score: dict[str, float] = defaultdict(float)
    turn: dict[str, int] = {}
    for side, ranking in enumerate((first, tools)):
        for rank, disease_id in enumerate(dict.fromkeys(ranking)):
            score[disease_id] += 1 / (RRF_K + rank)
            turn[disease_id] = min(turn.get(disease_id, 2 * rank + side), 2 * rank + side)
    return sorted(score, key=lambda d: (-score[d], turn[d]))


class Diagnosis(BaseModel):
    disease_id: str = Field(description="OMIM id, e.g. OMIM:621101")
    disease_name: str
    reason: str = Field(description="One sentence: the evidence for it, and against")


class FinalAnswer(BaseModel):
    """Your final answer: candidate diagnoses, most likely first."""

    diagnoses: list[Diagnosis] = Field(min_length=1, max_length=10)


class NoFinalAnswer(Exception):
    """The agent stopped without giving a final answer."""


def as_langchain_tool(tool: Any) -> BaseTool:
    """One of our tools as a LangChain tool: the same name, description and argument
    schema (the bound method's signature, without self), returning compact JSON."""
    call = tool.__call__

    @functools.wraps(call)
    def run(*args: Any, **kwargs: Any) -> str:
        return str(call(*args, **kwargs).model_dump_json())

    run.__signature__ = inspect.signature(call)  # type: ignore[attr-defined]
    run.__name__ = tool.name
    return StructuredTool.from_function(
        func=run, name=tool.name, description=inspect.getdoc(call) or tool.name
    )


@wrap_model_call
def _answer_on_the_last_turn(
    request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """On the last model call the budget allows, offer only the final-answer tool and say
    so. The reminder goes into this one request only, not into the conversation."""
    turns_taken = sum(isinstance(m, AIMessage) for m in request.messages)
    if turns_taken >= MAX_MODEL_CALLS - 1:
        request = request.override(tools=[], messages=[*request.messages, HumanMessage(LAST_TURN)])
    return handler(request)


def _error_for_model(error: Exception, request: Any) -> str | None:
    """A message for errors the model can fix; anything else fails the case."""
    if isinstance(error, UnknownDisease | ValidationError):
        return f"{request.tool_call['name']} failed: {error}"
    return None


class Agent:
    def __init__(
        self,
        model: BaseChatModel,
        model_name: str,
        hpo: HPO,
        *,
        seeded: bool = False,
        hypotheses: bool = False,
        prevalence: Mapping[str, str] | None = None,
        extra_tools: Sequence[Any] = (),
        name: str | None = None,
    ) -> None:
        """The four core tools, plus any extra ones (each named in GUIDES). `name` is the
        system's name in the evaluation; by default "agent", "seeded-agent" or
        "hypothesis-agent". A hypothesis agent is seeded too, with both lists; given
        `prevalence` (OMIM id -> Orphanet's class), each disease in them shows it."""
        self.model = model
        self.model_name = model_name
        self.hpo = hpo
        self.seeded = seeded or hypotheses
        self.hypotheses = hypotheses
        self.prevalence = prevalence
        default = "hypothesis-agent" if hypotheses else "seeded-agent" if seeded else "agent"
        self.name = name or default
        rank, check, lookup = RankDiseases(hpo), CheckMatch(hpo), LookupDisease(hpo)
        self.seed = RankThenCheck(rank, check)
        self.check, self.lookup, self.find = check, lookup, FindDisease(hpo)
        tools: list[Any] = [rank, check, lookup, self.find, *extra_tools]
        self.extra_tools = list(extra_tools)
        self.gene_rank = next(
            (GeneRank(t) for t in extra_tools if t.name == "rank_candidate_genes"), None
        )
        self.tool_names = [t.name for t in tools]
        unknown = [n for n in self.tool_names if n not in GUIDES]
        if unknown:
            raise ValueError(f"no prompt guide for tool(s) {', '.join(unknown)}")
        middleware: list[Any] = [  # each is typed for its own state; the agent combines them
            ModelCallLimitMiddleware(run_limit=MAX_MODEL_CALLS, exit_behavior="end"),
            _answer_on_the_last_turn,
            ToolErrorMiddleware(_error_for_model),
        ]
        self.graph = create_agent(
            model,
            tools=[as_langchain_tool(t) for t in tools],
            system_prompt=system_prompt(
                self.tool_names,
                seeded=seeded,
                hypotheses=hypotheses,
                prevalence=prevalence is not None,
            ),
            response_format=ToolStrategy(FinalAnswer),
            middleware=middleware,
        )

    def params(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.model_name,
            "thinking": False,
            "prompt_version": (
                HYPOTHESES_PREVALENCE_PROMPT_VERSION
                if self.prevalence is not None
                else HYPOTHESES_PROMPT_VERSION
            )
            if self.hypotheses
            else SEEDED_PROMPT_VERSION
            if self.seeded
            else PROMPT_VERSION,
            "max_model_calls": MAX_MODEL_CALLS,
            "tools": ", ".join(self.tool_names),
            "hpo_release": self.hpo.release,
        }
        if self.hypotheses:
            params |= {
                "first_answer": f"{llm_direct.PROMPT_VERSION}, each disease found by its "
                f"number, else by name (WRatio >= {NAME_MATCH}), and checked",
                "seed": f"rank-then-check top {SHOWN}",
                "fill": f"first answer and the tools' order, reciprocal rank (k={RRF_K})",
            }
            if self.prevalence is not None:
                params["prevalence"] = "Orphanet's class, by exact OMIM mapping"
        elif self.seeded:
            params |= {"seed": f"rank-then-check top {SHOWN}", "fill": "the tools' order"}
        for tool in self.extra_tools:
            if hasattr(tool, "bank_name"):
                params["patient_bank"] = tool.bank_name
        if self.gene_rank is not None:
            params["fusion"] = f"reciprocal rank (k={RRF_K}) with the candidate-gene ranking"
        return params

    def _first_answer(self, question: Question) -> list[Candidate]:
        """The model's answer before any tool ran: the single-call baseline's prompt and
        question. One repair attempt, as llm.ask_json; an answer still unreadable is none."""
        model = self.model.bind(response_format={"type": "json_object"})
        messages: list[BaseMessage] = [
            SystemMessage(llm_direct.SYSTEM_PROMPT),
            HumanMessage(user_prompt(question)),
        ]
        for _ in range(2):
            reply = model.invoke(messages)
            try:
                return llm_direct.parse(str(reply.content))
            except (ValueError, ValidationError) as error:
                messages += [
                    reply,
                    HumanMessage(
                        f"That reply was not in the required format ({error}). "
                        "Reply again with only the json object."
                    ),
                ]
        return []

    def _resolve(self, guess: Candidate) -> str | None:
        """The HPO disease a guess means (find_disease.resolve)."""
        return resolve(guess.disease_id, guess.disease_name, self.find)

    def _both_lists(self, question: Question, ordered: list[Any]) -> tuple[str, list[str]]:
        """The hypothesis agent's evidence: its first answer, each disease found by name
        and checked, then the tools' leading candidates; a disease already shown is only
        pointed to. Also the diseases the first answer named, in its order."""
        guesses = self._first_answer(question)
        lines, first = [H_TITLE], []
        shown: dict[str, str] = {}  # disease id -> the tag it was shown under
        for i, guess in enumerate(guesses, 1):
            tag, disease_id = f"H{i}", self._resolve(guess)
            written = f"{guess.disease_name} ({guess.disease_id or 'no id'})"
            if disease_id is None:
                lines.append(f"[{tag}] {written}: no disease of this name in the HPO annotations")
                continue
            first.append(disease_id)
            if disease_id in shown:
                lines.append(f"[{tag}] = [{shown[disease_id]}]")
                continue
            shown[disease_id] = tag
            head, *rest = self._evidence(question, disease_id)
            if normalize_omim(guess.disease_id) != disease_id:  # found by name instead
                head += f" (you wrote {written})"
            lines += [f"[{tag}] {head}", *rest]
        if not guesses:
            lines.append("(none: your first answer could not be read)")
        lines += ["", T_TITLE]
        for i, (match, report) in enumerate(ordered[:SHOWN], 1):
            tag = f"T{i}"
            if match.disease_id in shown:
                lines.append(f"[{tag}] = [{shown[match.disease_id]}] {report.disease_name}")
                continue
            shown[match.disease_id] = tag
            head, *rest = self._evidence(question, match.disease_id, report)
            lines += [f"[{tag}] {head}", *rest]
        return "\n".join(lines), first

    def _evidence(
        self, question: Question, disease_id: str, report: MatchReport | None = None
    ) -> list[str]:
        """A disease's evidence, as the fixed pipeline shows it, with how common it is."""
        report = report or self.check(question.hpo_ids, disease_id)
        head, *rest = evidence(report, self.lookup(disease_id, max_features=1))
        if self.prevalence is not None:
            head += f" · prevalence {self.prevalence.get(disease_id, 'unknown')} (Orphanet)"
        return [head, *rest]

    def _candidate(self, disease_id: str, reason: str) -> Candidate:
        genes = self.hpo.genes.get(disease_id, ())
        return Candidate(
            disease_name=self.hpo.names[disease_id],
            disease_id=disease_id,
            gene=genes[0] if len(genes) == 1 else None,
            reason=reason,
        )

    def predict(self, question: Question) -> list[Candidate]:
        prompt = user_prompt(question)
        first: list[str] = []
        if self.seeded:
            ordered = self.seed.ordered(question)
            if self.hypotheses:
                block, first = self._both_lists(question, ordered)
            else:
                shown = [(r, self.lookup(m.disease_id, max_features=1)) for m, r in ordered[:SHOWN]]
                block = candidates_block(shown)
            prompt += "\n\n" + block
        result = self.graph.invoke(
            {"messages": [HumanMessage(prompt)]},
            # A backstop only: each turn is several graph steps (middleware hooks, the
            # model, the tools); the model-call limit is what bounds a run.
            {"recursion_limit": 10 * MAX_MODEL_CALLS},
        )
        answer = result.get("structured_response")
        if not isinstance(answer, FinalAnswer):
            raise NoFinalAnswer(f"no final answer within {MAX_MODEL_CALLS} model calls")
        candidates: list[Candidate] = []
        for d in answer.diagnoses:
            disease_id = normalize_omim(d.disease_id)
            if disease_id is None or any(c.disease_id == disease_id for c in candidates):
                continue
            genes = self.hpo.genes.get(disease_id, ())
            candidates.append(
                Candidate(
                    disease_name=d.disease_name,
                    disease_id=disease_id,
                    gene=genes[0] if len(genes) == 1 else None,
                    reason=d.reason,
                )
            )
        if self.hypotheses:
            listed = {c.disease_id for c in candidates}
            for disease_id in merge(first, [m.disease_id for m, _ in ordered]):
                if len(candidates) >= 10:
                    break
                if disease_id not in listed:
                    candidates.append(self._candidate(disease_id, FILLED_BOTH))
        elif self.seeded:
            listed = {c.disease_id for c in candidates}
            for match, _ in ordered:
                if len(candidates) >= 10:
                    break
                if match.disease_id not in listed:
                    candidates.append(candidate(match).model_copy(update={"reason": FILLED}))
        if self.gene_rank is not None and question.candidate_genes:
            candidates = fuse(candidates, self.gene_rank.predict(question))
        return candidates

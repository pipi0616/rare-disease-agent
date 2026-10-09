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

The tools run in this process, so the evaluation's mask reaches them exactly as
it reaches the fixed pipeline's. The prompts are versioned like the baselines'.
"""

import functools
import inspect
from collections.abc import Callable, Sequence
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
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field, ValidationError

from raredx.baselines.fixed_pipeline import SHOWN, candidates_block
from raredx.baselines.llm_direct import user_prompt
from raredx.baselines.phenotype_rank import candidate
from raredx.baselines.rank_then_check import RankThenCheck
from raredx.evals.scoring import normalize_omim
from raredx.evals.systems import Candidate, Question
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.find_disease import FindDisease
from raredx.tools.ids import UnknownDisease
from raredx.tools.lookup_disease import LookupDisease
from raredx.tools.rank_diseases import RankDiseases

PROMPT_VERSION = "agent-v3"
SEEDED_PROMPT_VERSION = "seeded-v1"
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


def system_prompt(tools: list[str], *, seeded: bool = False) -> str:
    """The system prompt for an agent with these tools."""
    return f"{_role_and_tools(tools)}{_INVESTIGATE_SEEDED if seeded else _INVESTIGATE}"


FILLED = "Not ranked by the agent: filled in from the phenotype tools' order."


LAST_TURN = (
    "Your budget is spent: this is your last turn. Give your final answer now, with the "
    "FinalAnswer tool, from the evidence you have."
)


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
        extra_tools: Sequence[Any] = (),
        name: str | None = None,
    ) -> None:
        """The four core tools, plus any extra ones (each named in GUIDES). `name` is the
        system's name in the evaluation; by default "agent" or "seeded-agent"."""
        self.model_name = model_name
        self.hpo = hpo
        self.seeded = seeded
        self.name = name or ("seeded-agent" if seeded else "agent")
        rank, check, lookup = RankDiseases(hpo), CheckMatch(hpo), LookupDisease(hpo)
        self.seed = RankThenCheck(rank, check)
        self.lookup = lookup
        tools: list[Any] = [rank, check, lookup, FindDisease(hpo), *extra_tools]
        self.extra_tools = list(extra_tools)
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
            system_prompt=system_prompt(self.tool_names, seeded=seeded),
            response_format=ToolStrategy(FinalAnswer),
            middleware=middleware,
        )

    def params(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.model_name,
            "thinking": False,
            "prompt_version": SEEDED_PROMPT_VERSION if self.seeded else PROMPT_VERSION,
            "max_model_calls": MAX_MODEL_CALLS,
            "tools": ", ".join(self.tool_names),
            "hpo_release": self.hpo.release,
        }
        if self.seeded:
            params |= {"seed": f"rank-then-check top {SHOWN}", "fill": "the tools' order"}
        for tool in self.extra_tools:
            if hasattr(tool, "bank_name"):
                params["patient_bank"] = tool.bank_name
        return params

    def predict(self, question: Question) -> list[Candidate]:
        prompt = user_prompt(question)
        if self.seeded:
            ordered = self.seed.ordered(question)
            shown = [(r, self.lookup(m.disease_id, max_features=1)) for m, r in ordered[:SHOWN]]
            prompt += "\n\n" + candidates_block(shown)
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
        if self.seeded:
            listed = {c.disease_id for c in candidates}
            for match, _ in ordered:
                if len(candidates) >= 10:
                    break
                if match.disease_id not in listed:
                    candidates.append(candidate(match).model_copy(update={"reason": FILLED}))
        return candidates

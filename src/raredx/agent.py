"""The agent: the model decides what to look up, and when it has enough.

The same tools as the fixed pipeline, plus find_disease, and no fixed order.
The model calls tools in a loop — LangChain's create_agent, built on LangGraph —
until it gives its final answer: up to ten OMIM diseases, best first, each with
a reason. Unlike the fixed pipeline it can check a disease the ranking did not
propose: one it thinks of, found by name.

Bounds, all LangChain middleware:
- at most MAX_MODEL_CALLS model calls per case, and on the last one the model is
  offered only the final answer, so it must give one (a wrap_model_call
  middleware of ours; without it, the first runs investigated until they ran
  out). ModelCallLimitMiddleware stops a model that still does not answer; the
  case then fails, and scores as a miss;
- an error the model can fix — an unknown disease id, arguments that break a
  tool's schema — comes back to it as a message, so it can retry
  (ToolErrorMiddleware); anything else fails the case;
- the final answer is a schema the model must fill (ToolStrategy).

The tools run in this process, so the evaluation's mask reaches them exactly as
it reaches the fixed pipeline's. The prompt is versioned like the baselines'.
"""

import functools
import inspect
from collections.abc import Callable
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

from raredx.baselines.llm_direct import user_prompt
from raredx.evals.scoring import normalize_omim
from raredx.evals.systems import Candidate, Question
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.find_disease import FindDisease
from raredx.tools.ids import UnknownDisease
from raredx.tools.lookup_disease import LookupDisease
from raredx.tools.rank_diseases import RankDiseases

PROMPT_VERSION = "agent-v2"
MAX_MODEL_CALLS = 8

SYSTEM_PROMPT = f"""\
You are a clinical geneticist. Your task is to diagnose a patient with a suspected \
rare Mendelian disease from their phenotype, given as Human Phenotype Ontology (HPO) \
terms.

Your tools work over the HPO disease annotations:
- rank_diseases: every OMIM disease ranked by how well its phenotype matches. Start here.
- check_match: the patient's findings against one disease: which it explains, which it \
does not, which its patients were found not to have, and its frequent features the \
patient lacks.
- lookup_disease: one disease's features and their frequencies, inheritance, onset, genes.
- find_disease: the OMIM id of a disease you have in mind, by name.

Investigate before you answer. Check the leading candidates with check_match. The \
ranking can miss a disease with few annotations: if you suspect one it did not \
propose, find it by name and check it too. Weigh the evidence: a diagnosis should \
explain the patient's findings, above all the specific ones; findings recorded absent \
and missing hallmark features count against it; inheritance and onset should fit. You \
may name a disease the tools know little about if you have good reason.

Your budget is {MAX_MODEL_CALLS} turns, and the last one is for your answer. A few \
rounds are usually enough: rank, check the leading candidates (several calls at \
once), check any you suspect, then answer. When you have enough, give your final \
answer: up to 10 OMIM diseases, most likely first, each with a one-sentence reason."""


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
    """On the last model call the budget allows, offer only the final-answer tool."""
    turns_taken = sum(isinstance(m, AIMessage) for m in request.messages)
    if turns_taken >= MAX_MODEL_CALLS - 1:
        request = request.override(tools=[])
    return handler(request)


def _error_for_model(error: Exception, request: Any) -> str | None:
    """A message for errors the model can fix; anything else fails the case."""
    if isinstance(error, UnknownDisease | ValidationError):
        return f"{request.tool_call['name']} failed: {error}"
    return None


class Agent:
    name = "agent"

    def __init__(self, model: BaseChatModel, model_name: str, hpo: HPO) -> None:
        self.model_name = model_name
        self.hpo = hpo
        tools: list[RankDiseases | CheckMatch | LookupDisease | FindDisease] = [
            RankDiseases(hpo),
            CheckMatch(hpo),
            LookupDisease(hpo),
            FindDisease(hpo),
        ]
        self.tool_names = [t.name for t in tools]
        middleware: list[Any] = [  # each is typed for its own state; the agent combines them
            ModelCallLimitMiddleware(run_limit=MAX_MODEL_CALLS, exit_behavior="end"),
            _answer_on_the_last_turn,
            ToolErrorMiddleware(_error_for_model),
        ]
        self.graph = create_agent(
            model,
            tools=[as_langchain_tool(t) for t in tools],
            system_prompt=SYSTEM_PROMPT,
            response_format=ToolStrategy(FinalAnswer),
            middleware=middleware,
        )

    def params(self) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "thinking": False,
            "prompt_version": PROMPT_VERSION,
            "max_model_calls": MAX_MODEL_CALLS,
            "tools": ", ".join(self.tool_names),
            "hpo_release": self.hpo.release,
        }

    def predict(self, question: Question) -> list[Candidate]:
        result = self.graph.invoke(
            {"messages": [HumanMessage(user_prompt(question))]},
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
        return candidates

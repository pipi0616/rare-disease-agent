"""The model client: the OpenAI SDK pointed at an OpenAI-compatible endpoint.

DeepSeek speaks the OpenAI chat-completions API, so the standard SDK is the
client; switching provider is configuration, not code. MLflow's OpenAI
autologging is switched on here, so every model call — the prompt, the answer,
token counts, latency — is recorded as a span inside the trace of whatever
question it was made for.
"""

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from raredx.config import Settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


class MissingAPIKey(Exception):
    pass


class BudgetExceeded(Exception):
    """The run's spending cap is reached: no further model call is made."""


Provider = Literal["deepseek", "openrouter"]


class Budget:
    """A spending cap for one run, in US dollars, checked before every model call.

    A cap checked between runs cannot stop one run that costs more than expected;
    this one stops the run itself. OpenRouter reports what each call cost; calls in
    flight when the cap is reached still finish, so a run can go over by a few calls.
    """

    def __init__(self, usd: float) -> None:
        self.usd = usd
        self.spent = 0.0
        self._lock = threading.Lock()

    def check(self) -> None:
        with self._lock:
            if self.spent >= self.usd:
                raise BudgetExceeded(f"${self.spent:.4f} spent of a ${self.usd:.2f} cap")

    def add(self, usd: float) -> None:
        with self._lock:
            self.spent += usd


def cost_of(response: Any) -> float:
    """What a call cost, as OpenRouter reports it; 0 when the provider does not say."""
    usage = getattr(response, "usage", None)
    cost = getattr(usage, "cost", None) if usage is not None else None
    if cost is None and usage is not None:
        cost = (getattr(usage, "model_extra", None) or {}).get("cost")
    return float(cost or 0.0)


def api_key(settings: Settings) -> str:
    """The model API key. A key left empty — .env.example copied and not filled in —
    is a missing key, said here, not a 401 from the provider later."""
    key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else ""
    if not key.strip():
        raise MissingAPIKey("no model API key: put DEEPSEEK_API_KEY=... in .env (see .env.example)")
    return key


def client(settings: Settings) -> OpenAI:
    key = api_key(settings)
    import mlflow  # imported here: only model runs need it

    mlflow.openai.autolog()
    return OpenAI(
        base_url=settings.llm_base_url,
        api_key=key,
        timeout=180,
        max_retries=2,  # the SDK retries timeouts, rate limits and 5xx with backoff
    )


def openrouter_client(settings: Settings) -> OpenAI:
    """Other providers' models (OpenAI, Anthropic, Google) through OpenRouter's
    OpenAI-compatible endpoint: one account, one balance, the same SDK."""
    key = settings.openrouter_api_key.get_secret_value() if settings.openrouter_api_key else ""
    if not key.strip():
        raise MissingAPIKey("no OpenRouter key: put OPENROUTER_API_KEY=... in .env")
    import mlflow

    mlflow.openai.autolog()
    return OpenAI(base_url=settings.openrouter_base_url, api_key=key, timeout=180, max_retries=2)


def openrouter_spent(settings: Settings) -> float:
    """What the OpenRouter account has spent in all, in US dollars, as it reports it."""
    import httpx2

    key = settings.openrouter_api_key.get_secret_value() if settings.openrouter_api_key else ""
    response = httpx2.get(
        f"{settings.openrouter_base_url}/credits",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    response.raise_for_status()
    return float(response.json()["data"]["total_usage"])


def chat_model(
    settings: Settings, *, timeout: float = 180, max_retries: int = 2
) -> "BaseChatModel":
    """The same endpoint as a LangChain chat model, for agents.

    Reasoning mode off and temperature 0, as for the single-call baseline. MLflow's
    LangChain autologging traces each model call and tool call of an agent run.
    The defaults wait long and retry, as suits an evaluation; a service answering
    someone gives each call less time.
    """
    key = api_key(settings)
    import mlflow
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    mlflow.langchain.autolog()
    return ChatOpenAI(
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        api_key=SecretStr(key),
        temperature=0.0,
        timeout=timeout,
        max_retries=max_retries,
        extra_body={"thinking": {"type": "disabled"}},
    )


def _complete(
    api: OpenAI,
    model: str,
    messages: list[ChatCompletionMessageParam],
    thinking: bool,
    provider: Provider = "deepseek",
    budget: Budget | None = None,
) -> str | None:
    options: dict[str, Any] = {"response_format": {"type": "json_object"}}
    if provider == "openrouter":
        # OpenRouter's own switch for reasoning, whatever the provider calls it; and the
        # cost of each call in its answer, for the budget.
        options["extra_body"] = {"reasoning": {"enabled": thinking}, "usage": {"include": True}}
    else:
        options["extra_body"] = {"thinking": {"type": "enabled" if thinking else "disabled"}}
    if not thinking:  # temperature has no effect in thinking mode
        options["temperature"] = 0.0
    if budget is not None:
        budget.check()
    response = api.chat.completions.create(model=model, messages=messages, **options)
    if budget is not None:
        budget.add(cost_of(response))
    content: str | None = response.choices[0].message.content
    return content


def ask_json[T](
    api: OpenAI,
    model: str,
    messages: list[ChatCompletionMessageParam],
    parse: Callable[[str | None], T],
    *,
    thinking: bool = False,
    provider: Provider = "deepseek",
    budget: Budget | None = None,
) -> T:
    """One chat-completions call in JSON mode, parsed — with one repair attempt.

    A reply that parse rejects is shown its error once and asked again. A second
    failure is raised: recorded in the trace, and scored as a miss.
    """
    content = _complete(api, model, messages, thinking, provider, budget)
    try:
        return parse(content)
    except (ValueError, ValidationError) as first_error:
        repair: list[ChatCompletionMessageParam] = [
            *messages,
            {"role": "assistant", "content": content or ""},
            {
                "role": "user",
                "content": f"That reply was not in the required format ({first_error}). "
                "Reply again with only the json object.",
            },
        ]
        return parse(_complete(api, model, repair, thinking, provider, budget))

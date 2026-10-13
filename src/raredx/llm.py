"""The model client: the OpenAI SDK pointed at an OpenAI-compatible endpoint.

DeepSeek speaks the OpenAI chat-completions API, so the standard SDK is the
client; switching provider is configuration, not code. MLflow's OpenAI
autologging is switched on here, so every model call — the prompt, the answer,
token counts, latency — is recorded as a span inside the trace of whatever
question it was made for.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from raredx.config import Settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


class MissingAPIKey(Exception):
    pass


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
    api: OpenAI, model: str, messages: list[ChatCompletionMessageParam], thinking: bool
) -> str | None:
    options: dict[str, Any] = {
        "response_format": {"type": "json_object"},
        "extra_body": {"thinking": {"type": "enabled" if thinking else "disabled"}},
    }
    if not thinking:  # temperature has no effect in thinking mode
        options["temperature"] = 0.0
    response = api.chat.completions.create(model=model, messages=messages, **options)
    content: str | None = response.choices[0].message.content
    return content


def ask_json[T](
    api: OpenAI,
    model: str,
    messages: list[ChatCompletionMessageParam],
    parse: Callable[[str | None], T],
    *,
    thinking: bool = False,
) -> T:
    """One chat-completions call in JSON mode, parsed — with one repair attempt.

    A reply that parse rejects is shown its error once and asked again. A second
    failure is raised: recorded in the trace, and scored as a miss.
    """
    content = _complete(api, model, messages, thinking)
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
        return parse(_complete(api, model, repair, thinking))

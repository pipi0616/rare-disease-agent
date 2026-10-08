"""The model client: the OpenAI SDK pointed at an OpenAI-compatible endpoint.

DeepSeek speaks the OpenAI chat-completions API, so the standard SDK is the
client; switching provider is configuration, not code. MLflow's OpenAI
autologging is switched on here, so every model call — the prompt, the answer,
token counts, latency — is recorded as a span inside the trace of whatever
question it was made for.
"""

from openai import OpenAI

from raredx.config import Settings


class MissingAPIKey(Exception):
    pass


def client(settings: Settings) -> OpenAI:
    if settings.llm_api_key is None:
        raise MissingAPIKey("no model API key: put DEEPSEEK_API_KEY=... in .env (see .env.example)")
    from raredx.mlflow_setup import mlflow  # imported here: only model runs need it

    mlflow.openai.autolog()
    return OpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key.get_secret_value(),
        timeout=180,
        max_retries=2,  # the SDK retries timeouts, rate limits and 5xx with backoff
    )

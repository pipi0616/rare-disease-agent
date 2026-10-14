"""Runtime settings, read from environment variables and an optional .env file.

Every setting is prefixed RAREDX_ (RAREDX_DATA_DIR=...). The model API key is
the one exception: it is read from DEEPSEEK_API_KEY, the provider's standard
name, or RAREDX_LLM_API_KEY. Secrets live only in .env, which git ignores, and
are held as SecretStr so they never appear in logs or tracebacks.
"""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAREDX_", env_file=".env", extra="ignore")

    # Raw downloads and derived files. Never in git; `raredx data fetch` recreates it.
    data_dir: Path = Path("data")
    # Dataset registry and frozen manifests. In git: they define what is evaluated.
    evals_dir: Path = Path("evals")
    # MLflow: where evaluation runs are recorded. Local SQLite by default; point it at a
    # shared MLflow server (RAREDX_MLFLOW_TRACKING_URI) and nothing else changes.
    mlflow_tracking_uri: str = "sqlite:///mlflow.db"
    mlflow_artifact_root: Path = Path("mlruns")

    # The model: any OpenAI-compatible endpoint. DeepSeek here; a hospital's own vLLM
    # server would be a different base URL and model name, and no code change.
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-flash"
    llm_api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("RAREDX_LLM_API_KEY", "DEEPSEEK_API_KEY")
    )
    # OpenRouter: one account for other providers' models, which the evaluation calls
    # once per case to compare with the agent. A secret: .env only.
    openrouter_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("RAREDX_OPENROUTER_API_KEY", "OPENROUTER_API_KEY"),
    )
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # USD per million tokens, for each run's cost estimate: deepseek-flash at its peak
    # rate (api-docs.deepseek.com, 2026-10); off-peak is half. Input the provider has
    # cached — a prefix it saw recently, such as an agent's earlier turns — costs 1/50.
    llm_price_input: float = 0.30
    llm_price_cached_input: float = 0.006
    llm_price_output: float = 1.20

    # DeepRare's checkout, with its own environment in .venv (comparison runs only).
    deeprare_dir: Path = Path("third_party/DeepRare")
    # The `java` that runs LIRICAL (comparison runs only), version 17 or later. Unset:
    # the one on PATH, or a Homebrew OpenJDK.
    java: str | None = None

    # The HTTP service (`raredx serve`).
    # When set, every /v1 request must carry it as X-API-Key. A secret: .env only.
    service_api_key: SecretStr | None = None
    # Requests answered at once; one more gets 503 and a Retry-After. Each costs money.
    service_max_concurrent: int = 4
    # After this long the agent stops before its next model call, and the request is
    # answered by the no-model ranking. A request on the held-out set took about 13 s.
    service_deadline_seconds: float = 60.0
    # "evaluated": the patient bank the evaluation used (the design split), so what
    # answers is what was measured. "all": every published patient — more to find,
    # and a configuration no evaluation has scored.
    service_patient_bank: Literal["evaluated", "all"] = "evaluated"
    # The commit a container image was built from; a checkout reads it from git instead.
    build_version: str | None = None


settings = Settings()

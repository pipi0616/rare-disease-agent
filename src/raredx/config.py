"""Runtime settings, read from environment variables and an optional .env file.

Every setting is prefixed RAREDX_ (RAREDX_DATA_DIR=...). The model API key is
the one exception: it is read from DEEPSEEK_API_KEY, the provider's standard
name, or RAREDX_LLM_API_KEY. Secrets live only in .env, which git ignores, and
are held as SecretStr so they never appear in logs or tracebacks.
"""

from pathlib import Path

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
    # USD per million tokens, for each run's cost estimate: deepseek-flash at its peak
    # rate (api-docs.deepseek.com, 2026-10). Off-peak is half; cache hits cost less.
    llm_price_input: float = 0.30
    llm_price_output: float = 1.20


settings = Settings()

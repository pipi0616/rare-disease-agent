"""Runtime settings, read from environment variables and an optional .env file.

Every setting is prefixed RAREDX_ (RAREDX_DATA_DIR=...). Nothing here is
secret yet; API keys arrive with the first model call and live in the same
place, so there is exactly one way configuration enters the program.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAREDX_", env_file=".env", extra="ignore")

    # Raw downloads and derived files. Never in git; `raredx data fetch` recreates it.
    data_dir: Path = Path("data")
    # Dataset registry and frozen manifests. In git: they define what is evaluated.
    evals_dir: Path = Path("evals")


settings = Settings()

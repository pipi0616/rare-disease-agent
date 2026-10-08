"""The command line: thin wrappers, so the tests only check wiring and messages."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from raredx.cli import app

runner = CliRunner()
EVALS = Path(__file__).resolve().parents[1] / "evals"


def test_help_lists_the_command_groups() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "data" in result.output and "eval" in result.output


def test_stats_says_to_build_first_when_there_are_no_cases(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["data", "stats", "--data-dir", str(tmp_path), "--evals-dir", str(EVALS)]
    )
    assert result.exit_code == 1
    assert "raredx data build" in result.output


def test_build_says_to_fetch_first_when_the_download_is_missing(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["data", "build", "--data-dir", str(tmp_path), "--evals-dir", str(EVALS)]
    )
    assert result.exit_code == 1
    assert "raredx data fetch" in result.output


def test_heldout_needs_final(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["eval", "run", "--system", "oracle", "--split", "heldout", "--data-dir", str(tmp_path)],
    )
    assert result.exit_code == 1
    assert "--final" in result.output


def test_a_model_run_without_a_key_says_where_to_put_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from raredx.config import settings

    monkeypatch.setattr(settings, "llm_api_key", None)
    result = runner.invoke(app, ["llm", "check"])
    assert result.exit_code == 1
    assert "DEEPSEEK_API_KEY" in result.output

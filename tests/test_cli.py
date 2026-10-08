"""The command line: thin wrappers, so the tests only check wiring and messages."""

from pathlib import Path

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

"""The command line: thin wrappers, so the tests only check wiring and messages."""

from pathlib import Path

from typer.testing import CliRunner

from raredx.cli import app

runner = CliRunner()


def test_help_lists_the_data_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "data" in result.output


def test_stats_explains_when_the_archive_is_missing(tmp_path: Path) -> None:
    result = runner.invoke(app, ["data", "stats", "--data-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "raredx data fetch" in result.output

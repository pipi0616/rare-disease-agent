"""The command line: thin wrappers, so the tests only check wiring and messages."""

from pathlib import Path

import pytest
import typer
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


def test_fetch_names_the_registered_sources_when_asked_for_another(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["data", "fetch", "rarebench", "--data-dir", str(tmp_path), "--evals-dir", str(EVALS)]
    )
    assert result.exit_code == 1
    assert "phenopacket-store, hpo" in result.output


def test_the_phenotype_baseline_says_to_fetch_hpo_first(tmp_path: Path) -> None:
    from raredx.cli import _system

    with pytest.raises(typer.Exit):
        _system("phenotype-rank", [], EVALS, tmp_path)


def test_compare_names_the_problem_when_a_run_does_not_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from raredx.config import settings

    monkeypatch.setattr(settings, "mlflow_tracking_uri", f"sqlite:///{tmp_path / 'mlflow.db'}")
    monkeypatch.setattr(settings, "mlflow_artifact_root", tmp_path / "mlruns")
    result = runner.invoke(app, ["eval", "compare", "no-such-run", "nor-this-one"])
    assert result.exit_code == 1
    assert "raredx eval runs" in result.output


def test_without_takes_only_an_extra_tool_and_only_for_the_agents(tmp_path: Path) -> None:
    base = ["eval", "run", "--data-dir", str(tmp_path), "--evals-dir", str(EVALS)]
    result = runner.invoke(app, [*base, "--system", "agent", "--without", "rank_diseases"])
    assert result.exit_code == 1 and "find_similar_patients" in result.output
    result = runner.invoke(
        app, [*base, "--system", "phenotype-rank", "--without", "find_similar_patients"]
    )
    assert result.exit_code == 1 and "agents only" in result.output


def test_every_extra_tool_has_a_line_in_the_agent_prompt() -> None:
    from raredx.agent import GUIDES
    from raredx.cli import EXTRA_TOOLS

    assert set(EXTRA_TOOLS) <= set(GUIDES)


def test_index_says_to_fetch_the_texts_first(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["data", "index", "--data-dir", str(tmp_path), "--evals-dir", str(EVALS)]
    )
    assert result.exit_code == 1
    assert "raredx data fetch orphanet medlineplus" in result.output

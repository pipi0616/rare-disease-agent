"""The code version a run records, in a throwaway git repository."""

import subprocess
from pathlib import Path

import pytest

from raredx.evals.provenance import code_version


def git(*args: str) -> str:
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "code.py").write_text("x = 1\n")
    git("add", "-A")
    git("commit", "-q", "-m", "code")
    return tmp_path


def test_a_commit_that_only_adds_documentation_keeps_the_version(repo: Path) -> None:
    version = code_version()
    assert version == git("rev-parse", "--short", "HEAD")
    (repo / "notes.md").write_text("docs\n")
    git("add", "-A")
    git("commit", "-q", "-m", "docs")
    assert code_version() == version  # HEAD moved; what results depend on did not


def test_uncommitted_code_is_dirty_and_an_uncommitted_note_is_not(repo: Path) -> None:
    (repo / "notes.md").write_text("draft\n")
    assert not code_version().endswith("-dirty")
    (repo / "src" / "code.py").write_text("x = 2\n")
    assert code_version().endswith("-dirty")

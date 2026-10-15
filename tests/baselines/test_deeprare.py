"""DeepRare as a system, with a stand-in for its environment: no torch, no web, no cost.

The stand-in takes the place of DeepRare's Python and writes the answer DeepRare
writes — its final text, and what it sent its model — so the wrapper's part can be
checked: what it hands DeepRare, how its names become OMIM ids, what is traced.
"""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import mlflow
import pytest

from raredx.baselines.deeprare import (
    DeepRare,
    DeepRareAPIError,
    DeepRareNotSetUp,
    embed_queries,
    query_text,
    ranked_names,
)
from raredx.evals.systems import Question
from raredx.knowledge.hpo import HPO

FINAL = """## **Hearing-ovarian syndrome** (Rank #1/5)
### Diagnostic Reasoning: ...
## **Something nobody has described** (Rank #2/5)
## **Hearing retina syndrome** (Rank #3/5)
## References: [1] ..."""

KEYS = {"DEEPSEEK_API_KEY": "sk-test", "OPENROUTER_API_KEY": "sk-or-test"}


def checkout(tmp_path: Path, answer: Any) -> Path:
    """A DeepRare folder whose 'Python' writes the given answer (or crashes)."""
    folder = tmp_path / "DeepRare"
    (folder / "database").mkdir(parents=True)
    (folder / "database" / "RDS_embeddings.csv").write_text("_id\n")
    python = folder / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    body = (
        f"Path(sys.argv[4]).write_text({json.dumps(json.dumps(answer))})"
        if answer is not None
        else "sys.exit('torch is not installed')"
    )
    python.write_text(
        "#!/usr/bin/env python3\nimport json, os, sys\nfrom pathlib import Path\n"
        "case = json.loads(Path(sys.argv[3]).read_text())\n"
        "Path(sys.argv[2]).joinpath('seen.json').write_text("
        "json.dumps({'case': case, 'keys': [os.environ.get(k) for k in "
        "('DEEPSEEK_API_KEY', 'OPENROUTER_API_KEY')]}))\n" + body + "\n",
        encoding="utf-8",
    )
    python.chmod(0o755)
    return folder


def question() -> Question:
    return Question(
        case_id="1", hpo_ids=["HP:0000407", "HP:0000786"], hpo_labels=["a", "b"], sex=None
    )


def test_its_ranked_names_are_read_from_its_headings() -> None:
    assert ranked_names(FINAL) == [
        "Hearing-ovarian syndrome",
        "Something nobody has described",
        "Hearing retina syndrome",
    ]
    assert ranked_names(None) == [] and ranked_names("no headings at all") == []


def test_its_names_become_omim_ids_and_what_it_sent_its_model_is_traced(
    hpo: HPO, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    answer = {"final": FINAL, "read": {"prompts": ["web: PMID 1001 says ..."]}, "usage": {}}
    folder = checkout(tmp_path, answer)
    monkeypatch.setattr("raredx.baselines.deeprare.RUNNER", folder / "runner.py")
    system = DeepRare(hpo, folder, KEYS)
    candidates = system.predict(question())
    assert [c.disease_id for c in candidates] == ["OMIM:690001", None, "OMIM:690002"]
    assert candidates[1].disease_name == "Something nobody has described"
    seen = json.loads((folder / "seen.json").read_text())
    # it is given the findings with their names as this release writes them, and the keys
    assert seen["case"]["hpo_labels"] == ["Sensorineural hearing impairment", "Primary amenorrhea"]
    assert seen["keys"] == ["sk-test", "sk-or-test"]
    mlflow.flush_trace_async_logging()
    trace = mlflow.get_trace(mlflow.get_last_active_trace_id() or "")
    assert trace is not None
    [tool] = [s for s in trace.data.spans if s.name == "deeprare"]
    assert tool.span_type == "TOOL" and "PMID 1001" in json.dumps(tool.outputs)


def test_a_relative_folder_is_handed_on_whole(
    hpo: HPO, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The runner changes into DeepRare's folder; a relative path would no longer lead
    to it (the first check run lost every case to "No module named 'diagnosis'")."""
    answer = {"final": FINAL, "read": {}, "usage": {}}
    folder = checkout(tmp_path, answer)
    monkeypatch.chdir(tmp_path)
    system = DeepRare(hpo, Path("DeepRare"), KEYS)
    assert system.folder.is_absolute() and system.folder == folder.resolve()
    assert system.predict(question())[0].disease_id == "OMIM:690001"


def test_no_answer_fails_the_case_with_what_went_wrong(
    hpo: HPO, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lost = {"final": None, "error": "APIConnectionError('x')", "usage": {"api_errors": 2}}
    folder = checkout(tmp_path, lost)
    monkeypatch.setattr("raredx.baselines.deeprare.RUNNER", folder / "runner.py")
    with pytest.raises(DeepRareAPIError, match="gave no answer: APIConnectionError"):
        DeepRare(hpo, folder, KEYS).predict(question())  # a lost case: asked again later
    own = checkout(tmp_path / "own", {"final": None, "error": "KeyError('x')", "usage": {}})
    with pytest.raises(RuntimeError, match="gave no answer: KeyError") as failed:
        DeepRare(hpo, own, KEYS).predict(question())  # its own failure: its miss
    assert not isinstance(failed.value, DeepRareAPIError)
    crashed = checkout(tmp_path / "other", None)
    with pytest.raises(RuntimeError, match="torch is not installed"):
        DeepRare(hpo, crashed, KEYS).predict(question())


def test_without_its_environment_or_keys_it_says_what_is_missing(hpo: HPO, tmp_path: Path) -> None:
    with pytest.raises(DeepRareNotSetUp, match="own environment"):
        DeepRare(hpo, tmp_path / "nothing", KEYS)
    folder = checkout(tmp_path, {})
    with pytest.raises(DeepRareNotSetUp, match="OPENROUTER_API_KEY"):
        DeepRare(hpo, folder, {"DEEPSEEK_API_KEY": "sk"})


class Embedder:
    """Stands in for the OpenRouter client's embeddings: a vector per text, noting each call."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.embeddings = self

    def create(self, input: list[str], model: str) -> Any:  # noqa: A002 - the SDK's name
        self.calls.append(input)
        return SimpleNamespace(data=[SimpleNamespace(embedding=[float(len(t))]) for t in input])


def test_queries_are_embedded_once_ahead_and_handed_to_deeprare(
    hpo: HPO, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "queries.json"
    client = Embedder()
    assert embed_queries([query_text(["a", "b"]), "c", "c"], cache, client) == 2
    assert embed_queries([query_text(["a", "b"]), "d"], cache, client) == 1  # only the new one
    assert client.calls == [["a, b", "c"], ["d"]]
    assert json.loads(cache.read_text()) == {"a, b": [4.0], "c": [1.0], "d": [1.0]}
    folder = checkout(tmp_path, {"final": FINAL, "read": {}, "usage": {}})
    monkeypatch.setattr("raredx.baselines.deeprare.RUNNER", folder / "runner.py")
    DeepRare(hpo, folder, KEYS, cache).predict(question())
    seen = json.loads((folder / "seen.json").read_text())
    assert seen["case"]["embeddings_file"] == str(cache.resolve())


def test_each_answer_is_saved_as_it_arrives_and_read_back_instead_of_asking_again(
    hpo: HPO, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = checkout(tmp_path, {"final": FINAL, "read": {"prompts": ["x"]}, "usage": {}})
    monkeypatch.setattr("raredx.baselines.deeprare.RUNNER", folder / "runner.py")
    answers = tmp_path / "answers"
    first = DeepRare(hpo, folder, KEYS, answers=answers).predict(question())
    [saved] = list(answers.glob("*.json"))
    (folder / "seen.json").unlink()
    again = DeepRare(hpo, folder, KEYS, answers=answers).predict(question())  # e.g. after a crash
    assert again == first
    assert not (folder / "seen.json").exists()  # DeepRare was not run a second time
    assert json.loads(saved.read_text())["final"] == FINAL


def test_a_lost_case_is_not_saved_so_it_is_asked_again(
    hpo: HPO, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lost = {"final": None, "error": "x", "usage": {"api_errors": 1}}
    folder = checkout(tmp_path, lost)
    monkeypatch.setattr("raredx.baselines.deeprare.RUNNER", folder / "runner.py")
    answers = tmp_path / "answers"
    with pytest.raises(DeepRareAPIError):
        DeepRare(hpo, folder, KEYS, answers=answers).predict(question())
    assert not answers.exists() or not list(answers.glob("*.json"))

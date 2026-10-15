"""DeepRare, a published rare-disease diagnosis agent, as a system under evaluation.

DeepRare (2025) is the closest published work to this project: a multi-agent
system that, for a patient's HPO terms, asks two diagnosis web services
(PubCaseFinder, PhenoBrain), searches the web and PubMed, retrieves similar
published cases from a bank, has a model propose five diagnoses, checks each
against Orphanet, OMIM, PubMed, arXiv and Wikipedia, and reflects before its
final answer: five diseases, best first, with reasons and references.

It runs as published (deeprare_runner.py, in its own environment, once per
case) with the departures listed there: DeepSeek deepseek-flash as its model,
which is also this project's agent's model, so the two compare as designs on
one model; DuckDuckGo as its search engine; its public case bank.

Two things set it apart from every other system here:

- **It cannot be masked.** The web, PubCaseFinder, PhenoBrain and its case bank
  can all hold the patient's own report. The run is recorded as unmasked, and
  everything DeepRare sent its model — which carries everything it retrieved —
  is traced, so how often it read the patient's own paper can be counted.
- **It answers with names.** Its five diseases are matched to OMIM by name
  (rapidfuzz WRatio over the release's OMIM names, as tool find_disease does,
  without the mask); a name matching no OMIM disease closely enough counts as no
  answer at that rank. Its authors score with a model that judges whether a name
  denotes the confirmed diagnosis; that scoring is applied afterwards, to
  DeepRare and to the agent alike.
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import SpanType
from rapidfuzz import fuzz, process, utils

from raredx.evals.systems import Candidate, Question
from raredx.knowledge.hpo import HPO

TOP = 5
EMBEDDING = "openai/text-embedding-3-small"  # the model DeepRare's case bank was embedded with
QUERY_EMBEDDINGS = "query-embeddings.json"
SAVED_ANSWERS = "answers"
SETUP = "deepseek-flash, thinking off; duckduckgo; PubMed case bank"  # what an answer depends on
MATCH = 90  # least name similarity (0-100) for a name to count as that OMIM disease
TIMEOUT_SECONDS = 1800
RUNNER = Path(__file__).with_name("deeprare_runner.py")


class DeepRareNotSetUp(Exception):
    pass


class DeepRareAPIError(Exception):
    """DeepRare gave no answer because a service it calls failed — a model API, or
    PubCaseFinder, PhenoBrain, a web page: a lost case, not its miss (the harness
    counts it with the model-API failures, and it can be asked again)."""


def query_text(hpo_labels: list[str]) -> str:
    """What DeepRare embeds to find similar cases: the patient's findings, by name, in a
    line — its patient_info, as the runner builds it."""
    return ", ".join(hpo_labels)


def embed_queries(texts: list[str], cache: Path, client: Any) -> int:
    """Embed the texts not yet in the cache file (OpenAI's model, through OpenRouter),
    and add them; returns how many were embedded. With every case's query embedded
    beforehand, a run needs OpenRouter not at all: the same vectors, read from disk."""
    known: dict[str, list[float]] = json.loads(cache.read_text()) if cache.exists() else {}
    todo = [t for t in dict.fromkeys(texts) if t not in known]
    cache.parent.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(todo), 50):
        batch = todo[start : start + 50]
        response = client.embeddings.create(input=batch, model=EMBEDDING)
        for text, item in zip(batch, response.data, strict=True):
            known[text] = item.embedding
        cache.write_text(json.dumps(known))
    return len(todo)


def ranked_names(final: str | None) -> list[str]:
    """The diseases DeepRare's final answer ranks, best first. It writes each as a
    heading: "## **DISEASE NAME** (Rank #1/5)"."""
    found = re.findall(r"#+\s*\*\*(.+?)\*\*", final or "")
    names = [re.sub(r"\s*\(Rank.*$", "", name).strip(" *#:") for name in found]
    return [n for n in names if n][:TOP]


class DeepRare:
    name = "deeprare"

    def __init__(
        self,
        hpo: HPO,
        folder: Path,
        keys: dict[str, str],
        embeddings: Path | None = None,
        answers: Path | None = None,
    ) -> None:
        """`folder`: the DeepRare checkout, with its environment in .venv and its
        database downloaded; `keys`: DEEPSEEK_API_KEY and OPENROUTER_API_KEY;
        `embeddings`: queries embedded beforehand (embed_queries), if any; `answers`: a
        folder where each answer is saved the moment it arrives, and read back instead of
        asking DeepRare again — a run cut short costs nothing twice."""
        self.hpo = hpo
        self.embeddings = embeddings.resolve() if embeddings else None
        self.answers = answers.resolve() if answers else None
        self.folder = folder.resolve()  # the runner changes directory: no relative path survives
        self.python = self.folder / ".venv" / "bin" / "python"
        if (
            not self.python.exists()
            or not (self.folder / "database" / "RDS_embeddings.csv").exists()
        ):
            raise DeepRareNotSetUp(
                f"{folder} has no DeepRare set up: its checkout, its own environment in .venv "
                "and its database (huggingface dataset Angelakeke/DeepRare in database/)"
            )
        missing = [k for k in ("DEEPSEEK_API_KEY", "OPENROUTER_API_KEY") if not keys.get(k)]
        if missing:
            raise DeepRareNotSetUp(f"DeepRare needs {' and '.join(missing)} in .env")
        self.keys = keys

    def params(self) -> dict[str, str]:
        commit = subprocess.run(
            ["git", "-C", str(self.folder), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        return {
            "deeprare": commit or "unknown",
            "model": "deepseek-flash, thinking off (main and summariser)",
            "embeddings": "openai/text-embedding-3-small via OpenRouter",
            "web_search": "duckduckgo",
            "case_bank": "PubMed (public)",
            "answer": f"top {TOP} names, matched to OMIM by name (WRatio >= {MATCH})",
            "hpo_release": self.hpo.release,
        }

    def saved_answer(self, hpo_ids: list[str], hpo_labels: list[str]) -> Path | None:
        """Where the answer to these findings is saved, under this setup."""
        if self.answers is None:
            return None
        key = json.dumps({"hpo_ids": hpo_ids, "hpo_labels": hpo_labels, "setup": SETUP})
        return self.answers / f"{hashlib.sha256(key.encode()).hexdigest()[:24]}.json"

    @mlflow.trace(name="deeprare", span_type=SpanType.TOOL)
    def consult(self, hpo_ids: list[str], hpo_labels: list[str]) -> dict[str, Any]:
        """DeepRare's answer for these findings, and everything it sent its model — read
        back from where it was saved, when it was already given once."""
        saved = self.saved_answer(hpo_ids, hpo_labels)
        if saved is not None and saved.exists():
            kept: dict[str, Any] = json.loads(saved.read_text())
            return {**kept, "read_back_from": saved.name}
        with tempfile.TemporaryDirectory(prefix="deeprare-") as tmp:
            case, answer = Path(tmp) / "case.json", Path(tmp) / "answer.json"
            embeddings = str(self.embeddings) if self.embeddings else None
            case.write_text(
                json.dumps(
                    {"hpo_ids": hpo_ids, "hpo_labels": hpo_labels, "embeddings_file": embeddings}
                )
            )
            done = subprocess.run(
                [str(self.python), str(RUNNER), str(self.folder), str(case), str(answer)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env={**os.environ, **self.keys},
            )
            if not answer.exists():
                raise RuntimeError(f"DeepRare failed: {(done.stderr or done.stdout)[-500:]}")
            result: dict[str, Any] = json.loads(answer.read_text())
        if saved is not None and result.get("final") is not None:  # an answer, not a loss
            saved.parent.mkdir(parents=True, exist_ok=True)
            part = saved.with_suffix(".part")
            part.write_text(json.dumps(result, ensure_ascii=False))
            part.replace(saved)  # whole or not at all
        return result

    def omim(self, name: str) -> tuple[str, str] | None:
        """The OMIM disease whose name is closest to this one, if close enough."""
        hit = process.extractOne(
            name, self.hpo.names, scorer=fuzz.WRatio, processor=utils.default_process
        )
        if hit is None or hit[1] < MATCH:
            return None
        return hit[2], self.hpo.names[hit[2]]

    def predict(self, question: Question) -> list[Candidate]:
        labels = [self.hpo.term(t)[1] for t in question.hpo_ids]
        answer = self.consult(question.hpo_ids, labels)
        if answer.get("final") is None:
            if (answer.get("usage") or {}).get("api_errors"):
                raise DeepRareAPIError(f"DeepRare gave no answer: {answer.get('error')}")
            raise RuntimeError(f"DeepRare gave no answer: {answer.get('error')}")
        candidates = []
        for name in ranked_names(answer["final"]):
            found = self.omim(name)
            candidates.append(Candidate(disease_name=name, disease_id=found[0] if found else None))
        return candidates

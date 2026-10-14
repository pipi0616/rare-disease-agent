"""The results report's datasets, computed from the project's own records.

Every figure on the report page comes from one of the JSON files this writes,
and each of those from the per-case tables in docs/ and the MLflow runs in the
local store. Run from the project root, after the evaluations:

    uv run python scripts/report_data.py <folder>
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from mlflow import MlflowClient

from raredx.data import cases as case_store
from raredx.evals.scoring import p_value, sign_test, wilson
from raredx.knowledge import prevalence
from raredx.phenotyping.evaluation import paired, per_document

STORE = "sqlite:///mlflow.db"
Row = dict[str, str]


def read_tsv(path: str) -> list[Row]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write(folder: Path, name: str, rows: list[dict[str, Any]]) -> None:
    (folder / name).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")


def pct(x: float) -> float:
    return round(100 * x, 1)


def rate(rows: list[Row], column: str) -> tuple[float, float, float]:
    """The share of rows hit in this column, and its 95% Wilson interval, in percent."""
    hits = sum(r[column] == "1" for r in rows)
    low, high = wilson(hits, len(rows))
    return pct(hits / len(rows)), pct(low), pct(high)


def against(rows: list[Row], a: str, b: str, k: int) -> tuple[int, int, str]:
    """Cases only a gets right at rank k, cases only b does, and the sign test."""
    wins = sum(r[f"{a}@{k}"] == "1" and r[f"{b}@{k}"] == "0" for r in rows)
    losses = sum(r[f"{b}@{k}"] == "1" and r[f"{a}@{k}"] == "0" for r in rows)
    return wins, losses, p_value(sign_test(wins, losses))


OUTSIDE = (
    ("agent", "This agent (deepseek-flash with tools)", "agent"),
    ("gpt", "GPT-6.1, asked directly", "frontier model"),
    ("lirical", "LIRICAL 2.4.1", "established tool"),
    ("gemini", "Gemini 4, asked directly", "frontier model"),
    ("claude", "Claude Sonnet 5.5, asked directly", "frontier model"),
    ("llm-direct", "deepseek-flash, asked directly", "the agent's model alone"),
)


def outside(rows: list[Row]) -> list[dict[str, Any]]:
    """Every outside system on the same 200 held-out cases."""
    out = []
    for key, name, kind in OUTSIDE:
        top1, top1_low, top1_high = rate(rows, f"{key}@1")
        top10, top10_low, top10_high = rate(rows, f"{key}@10")
        wins, losses, p = against(rows, "agent", key, 1) if key != "agent" else (None, None, None)
        out.append(
            {"system": name, "kind": kind, "top1": top1, "top1_low": top1_low,
             "top1_high": top1_high, "top10": top10, "top10_low": top10_low,
             "top10_high": top10_high, "agent_wins": wins, "agent_losses": losses, "p": p}
        )  # fmt: skip
    return out


def deeprare(rows: list[Row], judged: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The agent and DeepRare by OMIM id and by DeepRare's own LLM judge, at 1 and 5."""

    def hit(x: dict[str, Any], system: str, k: int) -> bool:
        return x[system] is not None and x[system] <= k

    out = []
    for k in (1, 5):
        wins, losses, p = against(rows, "agent", "deeprare", k)
        out.append(
            {"scoring": "by OMIM id", "rank": f"top {k}", "agent": rate(rows, f"agent@{k}")[0],
             "deeprare": rate(rows, f"deeprare@{k}")[0], "agent_wins": wins,
             "deeprare_wins": losses, "p": p}
        )  # fmt: skip
        wins = sum(hit(x, "agent", k) and not hit(x, "deeprare", k) for x in judged)
        losses = sum(hit(x, "deeprare", k) and not hit(x, "agent", k) for x in judged)
        out.append(
            {"scoring": "judged (DeepRare's own)", "rank": f"top {k}",
             "agent": pct(sum(hit(x, "agent", k) for x in judged) / len(judged)),
             "deeprare": pct(sum(hit(x, "deeprare", k) for x in judged) / len(judged)),
             "agent_wins": wins, "deeprare_wins": losses, "p": p_value(sign_test(wins, losses))}
        )  # fmt: skip
    for row in out:
        row["key"] = f"{row['scoring']} · {row['rank']}"
    return out


HELDOUT = (  # MLflow run (first 8 characters), as the report names it, track
    ("5df45fbd", "This agent", "phenotype"),
    ("188cc460", "Fixed pipeline (one model call)", "phenotype"),
    ("59ff68e3", "Rank, then check (no model)", "phenotype"),
    ("e1e02e75", "LIRICAL 2.4.1", "phenotype"),
    ("82a405ec", "Nearest published patients (no model)", "phenotype"),
    ("c683f1fd", "Phenotype similarity (no model)", "phenotype"),
    ("2c99bb1e", "deepseek-flash, asked directly", "phenotype"),
    ("1790ea15", "This agent, with candidate genes", "with genes"),
    ("69e254da", "Gene ranking (no model), with candidate genes", "with genes"),
)


def heldout(client: MlflowClient) -> list[dict[str, Any]]:
    """The full held-out set, as its MLflow runs recorded it."""
    names = ("eval/heldout-papers", "eval/heldout-papers+genes")
    runs = {
        r.info.run_id[:8]: r
        for e in client.search_experiments()
        if e.name in names
        for r in client.search_runs([e.experiment_id])
    }
    out = []
    for short, name, track in HELDOUT:
        run = runs[short]
        m = run.data.metrics
        out.append(
            {"system": name, "track": track, "cases": int(m["n_cases"]),
             "top1": pct(m["disease_top1/mean"]), "top1_low": pct(m["disease_top1/low"]),
             "top1_high": pct(m["disease_top1/high"]), "top10": pct(m["disease_top10/mean"]),
             "top10_low": pct(m["disease_top10/low"]), "top10_high": pct(m["disease_top10/high"]),
             "mlflow_run": run.info.run_id}
        )  # fmt: skip
    return out


def by_prevalence(rows: list[Row]) -> list[dict[str, Any]]:
    """The 840 held-out cases by the Orphanet prevalence class of the confirmed disease."""
    band = prevalence.omim_bands(
        Path("data/raw/orphanet-prevalence/2026-06-23/en_product9_prev.xml"),
        Path("data/raw/orphanet/2026-06-23/en_product1.xml"),
    )
    disease = {
        c.id: c.disease_id for c in case_store.read(Path("data/processed/phenopacket-store/0.1.27"))
    }
    groups: dict[str, list[Row]] = defaultdict(list)
    for r in rows:
        groups[band.get(disease[r["case_id"]], "unknown")].append(r)
    return [
        {"band": "not classed by Orphanet" if b == "unknown" else b, "cases": len(groups[b]),
         "diseases": len({disease[r["case_id"]] for r in groups[b]}),
         "agent": rate(groups[b], "agent@1")[0], "model_alone": rate(groups[b], "llm-direct@1")[0],
         "lirical": rate(groups[b], "lirical@1")[0],
         "fixed_pipeline": rate(groups[b], "fixed-pipeline@1")[0]}
        for b in prevalence.BANDS
    ]  # fmt: skip


NOTE_RUNS = {
    "ID-68": {
        "note-reader": "14c70addb09248b7a7c38132a0026432",
        "dictionary": "d0909c288c274e318d5f18de0955c800",
        "model-direct": "c6e2207f3e724e75800de16b5abd4141",
    },
    "GSC-2024": {
        "note-reader": "8f2651c9859d467682539040fe8ba25f",
        "dictionary": "450eee70d7f246bd8e6f3e810886e4f9",
        "model-direct": "7971168e532d4fec98b466b2e65ace67",
    },
}
READER = {
    "note-reader": "This reader",
    "dictionary": "Dictionary of HPO names",
    "model-direct": "The model writing HPO ids itself",
}
AUTOPCR = {"ID-68": 80.3, "GSC-2024": 83.5}  # its published document-level F1


def notes(client: MlflowClient) -> list[dict[str, Any]]:
    """The three readers on both test sets, paired against this one; AutoPCR as published."""
    out: list[dict[str, Any]] = []
    for corpus, runs in NOTE_RUNS.items():
        scored = {reader: per_document(STORE, run) for reader, run in runs.items()}
        for reader, run in runs.items():
            m = client.get_run(run).data.metrics
            wins = losses = p = None
            if reader != "note-reader":
                wins, losses, sign = paired(scored["note-reader"], scored[reader])
                p = p_value(sign)
            out.append(
                {"key": f"{corpus} · {READER[reader]}", "corpus": corpus,
                 "reader": READER[reader], "precision": pct(m["micro/precision"]),
                 "recall": pct(m["micro/recall"]), "f1": pct(m["micro/f1"]),
                 "reader_wins": wins, "reader_losses": losses, "p": p, "mlflow_run": run}
            )  # fmt: skip
        out.append(
            {"key": f"{corpus} · AutoPCR (published)", "corpus": corpus,
             "reader": "AutoPCR (published, HPO 2024)", "precision": None, "recall": None,
             "f1": AUTOPCR[corpus], "reader_wins": None, "reader_losses": None, "p": None,
             "mlflow_run": None}
        )  # fmt: skip
    return out


def cost(client: MlflowClient) -> list[dict[str, Any]]:
    """Time and money per case. The agent's from its held-out run; DeepRare's as summed
    from its traces (chapter 25); the frontier models' as OpenRouter billed them."""
    agent = next(
        r for e in client.search_experiments() if e.name == "eval/heldout-papers"
        for r in client.search_runs([e.experiment_id]) if r.info.run_id.startswith("5df45fbd")
    ).data.metrics  # fmt: skip
    peak = "estimated from tokens at deepseek-flash's peak price"
    return [
        {"system": "This agent", "seconds": round(agent["usage/seconds_per_case"], 1),
         "usd": round(agent["usage/cost_usd_estimate"] / agent["n_cases"], 4),
         "model_calls": "4–8", "basis": f"{peak}; 840 held-out cases (MLflow run 5df45fbd)"},
        {"system": "DeepRare, same model", "seconds": 194.0, "usd": 0.0136,
         "model_calls": "about 27",
         "basis": "estimated from tokens at the same price; 200 held-out cases "
                  "(MLflow run 56056f39)"},
        {"system": "GPT-6.1, asked directly", "seconds": 16.3, "usd": round(1.4402 / 200, 4),
         "model_calls": "1", "basis": "billed by OpenRouter; 200 cases"},
        {"system": "Claude Sonnet 5.5, asked directly", "seconds": 5.0,
         "usd": round(1.9492 / 200, 4), "model_calls": "1",
         "basis": "billed by OpenRouter; 200 cases, two runs (one completing the other)"},
        {"system": "Gemini 4, asked directly", "seconds": 5.3, "usd": round(1.1042 / 200, 4),
         "model_calls": "1",
         "basis": "billed by OpenRouter; 200 cases, two runs (one completing the other)"},
    ]  # fmt: skip


def main() -> None:
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    client = MlflowClient(STORE)
    rows200 = read_tsv("docs/comparison_llm_hits.tsv")
    judged = json.loads(Path("docs/deeprare_lenient.json").read_text())
    write(folder, "outside200.json", outside(rows200))
    write(folder, "deeprare.json", deeprare(rows200, judged))
    write(folder, "heldout840.json", heldout(client))
    write(folder, "prevalence.json", by_prevalence(read_tsv("docs/comparison_hits.tsv")))
    write(folder, "notes.json", notes(client))
    write(folder, "cost.json", cost(client))
    for f in sorted(folder.glob("*.json")):
        print(f"wrote {f}")


if __name__ == "__main__":
    main()

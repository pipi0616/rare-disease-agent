"""The `raredx` command line. Thin: every command calls into the package and prints."""

import statistics
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, NoReturn

import typer

from raredx.config import settings
from raredx.data import cases as case_store
from raredx.data import phenopackets, sources
from raredx.data.cases import Case
from raredx.evals import scoring, splits
from raredx.evals.provenance import code_version
from raredx.evals.systems import Oracle, Popularity, System

if TYPE_CHECKING:
    from raredx.evals.harness import Harness

app = typer.Typer(help="raredx — rare-disease diagnosis agent.", no_args_is_help=True)
data_app = typer.Typer(help="Datasets: fetch, build and inspect.", no_args_is_help=True)
eval_app = typer.Typer(help="Evaluation: manifests, runs and scores.", no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(eval_app, name="eval")
llm_app = typer.Typer(help="The model endpoint.", no_args_is_help=True)
app.add_typer(llm_app, name="llm")

DATASET = "phenopacket-store"

DataDir = Annotated[
    Path, typer.Option(help="Raw and processed data. Default: RAREDX_DATA_DIR or ./data.")
]
EvalsDir = Annotated[
    Path, typer.Option(help="Registry and manifests. Default: RAREDX_EVALS_DIR or ./evals.")
]


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


def _source(evals_dir: Path) -> sources.Source:
    return sources.load_sources(evals_dir / "datasets.toml")[DATASET]


def _processed(data_dir: Path, evals_dir: Path) -> tuple[Path, list[Case]]:
    out_dir = sources.processed_dir(_source(evals_dir), data_dir)
    if not (out_dir / case_store.CASES_FILE).exists():
        _fail(f"{out_dir} has no cases yet — run `raredx data build` first")
    return out_dir, case_store.read(out_dir)


# ── data ────────────────────────────────────────────────────────────


@data_app.command()
def fetch(
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
    force: bool = False,
) -> None:
    """Download the dataset into data/raw and verify its checksum."""
    source = _source(evals_dir)
    path = sources.fetch(source, data_dir, force=force)
    typer.echo(f"ok  {path}  ({source.name} {source.version}, sha256 verified)")


@data_app.command()
def build(data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir) -> None:
    """Parse the raw download into data/processed: one case per line."""
    source = _source(evals_dir)
    raw = sources.raw_path(source, data_dir)
    if not raw.exists():
        _fail(f"{raw} missing — run `raredx data fetch` first")
    cases, skipped = phenopackets.load(raw)
    info = {
        "source": source.name,
        "version": source.version,
        "raw_sha256": source.sha256,
        "cases": len(cases),
        "skipped": dict(skipped),
    }
    path = case_store.write(cases, sources.processed_dir(source, data_dir), info)
    typer.echo(f"ok  {path}  ({len(cases)} cases, skipped {dict(skipped) or 'none'})")


@data_app.command()
def stats(data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir) -> None:
    """Summarise the processed cases."""
    out_dir, cases = _processed(data_dir, evals_dir)
    info = case_store.read_build_info(out_dir)
    n_terms = [len(c.hpo_ids) for c in cases]
    terms = f"{statistics.median(n_terms):.0f} ({min(n_terms)}–{max(n_terms)})"
    split = (
        f"{sum(c.split == 'design' for c in cases)} / {sum(c.split == 'heldout' for c in cases)}"
    )
    rows = [
        ("cases", len(cases)),
        ("skipped", info["skipped"] or "none"),
        ("with a causal gene", sum(c.gene is not None for c in cases)),
        ("distinct diseases (OMIM)", len({c.disease_id for c in cases})),
        ("distinct genes", len({c.gene for c in cases if c.gene})),
        ("distinct source papers (PMID)", len({c.pmid for c in cases})),
        ("HPO terms per case, median (min–max)", terms),
        ("split design / heldout", split),
    ]
    for label, value in rows:
        typer.echo(f"{label:<40} {value}")


# ── eval ────────────────────────────────────────────────────────────


@eval_app.command("splits")
def make_splits(
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
    force: bool = False,
) -> None:
    """Create the manifests in evals/splits, or confirm they are unchanged."""
    _, cases = _processed(data_dir, evals_dir)
    try:
        status = splits.make_all(cases, evals_dir / "splits", force=force)
    except splits.FrozenManifestError as e:
        _fail(str(e))
    for name, state in status.items():
        typer.echo(f"{state:<10} {evals_dir / 'splits' / name}.tsv")


@eval_app.command()
def check(
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
    splits_dir: Annotated[Path | None, typer.Option(help="Default: <evals-dir>/splits.")] = None,
) -> None:
    """Check the manifests: their own rules, and against the data when it is present."""
    folder = splits_dir or evals_dir / "splits"
    problems = splits.check(folder)
    out_dir = sources.processed_dir(_source(evals_dir), data_dir)
    if not problems and (out_dir / case_store.CASES_FILE).exists():
        problems = splits.check_against(case_store.read(out_dir), folder)
    for problem in problems:
        typer.echo(f"problem  {problem}")
    if problems:
        raise typer.Exit(1)
    typer.echo(f"ok  {folder}: {', '.join(splits.NAMES)} pass every rule")


def _system(name: str, cases: list[Case], evals_dir: Path) -> System:
    if name == "oracle":
        return Oracle.from_cases(cases)
    if name == "popularity":
        dev_papers = {pmid for _, pmid in splits.read(evals_dir / "splits" / "dev-200.tsv")}
        pool = [c for c in cases if c.split == "design" and c.pmid not in dev_papers]
        return Popularity.from_cases(pool)
    if name in ("llm-direct", "llm-direct-thinking"):
        from raredx import llm
        from raredx.baselines.llm_direct import LLMDirect

        try:
            client = llm.client(settings)
        except llm.MissingAPIKey as e:
            _fail(str(e))
        return LLMDirect(client, settings.llm_model, thinking=name == "llm-direct-thinking")
    _fail(f"unknown system {name!r}: choose oracle, popularity, llm-direct or llm-direct-thinking")


def _harness() -> "Harness":
    from raredx.evals.harness import Harness  # imported here: mlflow is slow to load

    return Harness(settings.mlflow_tracking_uri, settings.mlflow_artifact_root)


def _manifest(evals_dir: Path, split: str) -> Path:
    manifest = evals_dir / "splits" / f"{split}.tsv"
    if not manifest.exists():
        _fail(f"{manifest} not found")
    return manifest


@eval_app.command("run")
def run_system(
    system: Annotated[
        str, typer.Option(help="oracle | popularity | llm-direct | llm-direct-thinking")
    ],
    split: Annotated[str, typer.Option(help="Manifest to run on.")] = "dev-200",
    final: Annotated[bool, typer.Option(help="Required for heldout: the final run.")] = False,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Evaluate a system on a manifest with MLflow; the run and every answer are recorded."""
    if split == "heldout" and not final:
        _fail("heldout is the final exam: run it once, with --final, when the design is frozen")
    out_dir, cases = _processed(data_dir, evals_dir)
    manifest = _manifest(evals_dir, split)
    by_id = {c.id: c for c in cases}
    selected = [by_id[case_id] for case_id, _ in splits.read(manifest)]
    chosen = _system(system, cases, evals_dir)
    build = case_store.read_build_info(out_dir)
    manifest_sha256 = sources.sha256_of(manifest)
    params = {
        "system": chosen.name,
        "manifest": split,
        "manifest_sha256": manifest_sha256,
        "dataset": f"{build['source']} {build['version']}",
        "dataset_sha256": build["raw_sha256"],
        "code": code_version(),
    }
    system_params = getattr(chosen, "params", None)
    if callable(system_params):  # e.g. the model, thinking mode and prompt version
        params.update(system_params())
    from raredx.evals.harness import IncompleteRun

    harness = _harness()
    try:
        run_id, summary = harness.evaluate(chosen, split, manifest_sha256, selected, params)
    except IncompleteRun as e:
        _fail(str(e))
    usage = harness.usage(run_id)
    tokens_in, tokens_out = usage["usage/input_tokens"], usage["usage/output_tokens"]
    if tokens_in or tokens_out:
        cost = (tokens_in * settings.llm_price_input + tokens_out * settings.llm_price_output) / 1e6
        usage["usage/cost_usd_estimate"] = round(cost, 4)
        harness.log_metrics(run_id, usage)
    typer.echo(scoring.render(summary, f"{chosen.name} · {split}"))
    if summary.n_answered < summary.n_cases:
        missing = summary.n_cases - summary.n_answered
        typer.echo(f"note: {missing} cases got no answer; their traces in MLflow show why")
    if tokens_in or tokens_out:
        typer.echo(
            f"usage: {tokens_in:,.0f} input + {tokens_out:,.0f} output tokens, "
            f"about ${usage['usage/cost_usd_estimate']:.2f} at peak price; "
            f"{usage['usage/seconds_per_case']:.1f} s per case"
        )
    typer.echo(f"recorded in MLflow: experiment eval/{split}, run {run_id}")


@eval_app.command("score")
def score_run(
    run_id: Annotated[str, typer.Argument(help="An MLflow run id, from `raredx eval runs`.")],
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Score a recorded run again from its traces, as a new run. Nothing is re-asked."""
    harness = _harness()
    params = dict(harness.client.get_run(run_id).data.params)
    manifest = _manifest(evals_dir, params["manifest"])
    from raredx.evals.harness import IncompleteRun, ManifestMismatch

    expected = len(splits.read(manifest))
    try:
        new_id, summary, _ = harness.rescore(run_id, sources.sha256_of(manifest), expected)
    except (ManifestMismatch, IncompleteRun) as e:
        _fail(str(e))
    typer.echo(scoring.render(summary, f"{params['system']} · {params['manifest']} · rescored"))
    typer.echo(f"recorded in MLflow: experiment eval/{params['manifest']}, run {new_id}")


@eval_app.command("runs")
def list_runs(
    split: Annotated[str, typer.Option(help="Manifest whose runs to list.")] = "dev-200",
) -> None:
    """List the recorded runs on a manifest, newest first."""
    rows = _harness().runs(split)
    if not rows:
        typer.echo(f"no runs recorded on {split} yet")
        return

    def pct(value: float | None) -> str:
        return "" if value is None else f"{value * 100:.1f}%"

    header = ("started", "run", "disease@1", "disease@10", "gene@10", "code", "run id")
    typer.echo("{:<17} {:<24} {:>9} {:>10} {:>8}  {:<14} {}".format(*header))
    for r in rows:
        started = datetime.fromtimestamp(r["start_time"] / 1000).strftime("%Y-%m-%d %H:%M")
        scores = [pct(r["disease_top1"]), pct(r["disease_top10"]), pct(r["gene_top10"])]
        cells = [started, r["name"], *scores, r["code"], r["run_id"]]
        typer.echo("{:<17} {:<24} {:>9} {:>10} {:>8}  {:<14} {}".format(*cells))


# ── llm ─────────────────────────────────────────────────────────────


@llm_app.command("check")
def llm_check() -> None:
    """Check the API key and the endpoint, and list its models. Costs nothing."""
    from raredx import llm

    try:
        client = llm.client(settings)
    except llm.MissingAPIKey as e:
        _fail(str(e))
    models = sorted(m.id for m in client.models.list())
    typer.echo(f"endpoint  {settings.llm_base_url}  (key found in .env)")
    typer.echo(f"models    {', '.join(models)}")
    marker = "available" if settings.llm_model in models else "NOT AVAILABLE"
    typer.echo(f"using     {settings.llm_model}  ({marker})")

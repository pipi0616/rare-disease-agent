"""The `raredx` command line. Thin: every command calls into the package and prints."""

import statistics
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from raredx.config import settings
from raredx.data import cases as case_store
from raredx.data import phenopackets, sources
from raredx.data.cases import Case
from raredx.evals import runs, scoring, splits
from raredx.evals.systems import Oracle, Popularity, System

app = typer.Typer(help="raredx — rare-disease diagnosis agent.", no_args_is_help=True)
data_app = typer.Typer(help="Datasets: fetch, build and inspect.", no_args_is_help=True)
eval_app = typer.Typer(help="Evaluation: manifests, runs and scores.", no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(eval_app, name="eval")

DATASET = "phenopacket-store"

DataDir = Annotated[
    Path, typer.Option(help="Raw and processed data. Default: RAREDX_DATA_DIR or ./data.")
]
EvalsDir = Annotated[
    Path, typer.Option(help="Registry and manifests. Default: RAREDX_EVALS_DIR or ./evals.")
]
RunsDir = Annotated[Path, typer.Option(help="Run folders. Default: RAREDX_RUNS_DIR or ./runs.")]


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
    _fail(f"unknown system {name!r}: choose oracle or popularity")


@eval_app.command("run")
def run_system(
    system: Annotated[str, typer.Option(help="oracle | popularity")],
    split: Annotated[str, typer.Option(help="Manifest to run on.")] = "dev-200",
    final: Annotated[bool, typer.Option(help="Required for heldout: the final run.")] = False,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
    runs_dir: RunsDir = settings.runs_dir,
) -> None:
    """Run a system on a manifest, save its answers in runs/, and score them."""
    if split == "heldout" and not final:
        _fail("heldout is the final exam: run it once, with --final, when the design is frozen")
    out_dir, cases = _processed(data_dir, evals_dir)
    manifest = evals_dir / "splits" / f"{split}.tsv"
    if not manifest.exists():
        _fail(f"{manifest} not found")
    by_id = {c.id: c for c in cases}
    selected = [by_id[case_id] for case_id, _ in splits.read(manifest)]
    chosen = _system(system, cases, evals_dir)
    run_dir = runs.start(runs_dir, chosen.name, manifest, case_store.read_build_info(out_dir))
    runs.execute(chosen, selected, run_dir)
    summary = runs.score(run_dir, by_id)
    typer.echo(scoring.render(summary, f"{chosen.name} · {split}"))
    typer.echo(f"saved  {run_dir}")


@eval_app.command("score")
def score_run(
    run_dir: Annotated[Path, typer.Argument(help="A folder under runs/.")],
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Score a saved run again, without running the system."""
    _, cases = _processed(data_dir, evals_dir)
    try:
        summary = runs.score(run_dir, {c.id: c for c in cases})
    except ValueError as e:
        _fail(str(e))
    meta = runs.read_meta(run_dir)
    typer.echo(scoring.render(summary, f"{meta['system']} · {Path(meta['manifest']).stem}"))

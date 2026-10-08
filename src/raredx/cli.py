"""The `raredx` command line. Thin: every command calls into the package and prints."""

import statistics
from pathlib import Path
from typing import Annotated

import typer

from raredx.config import settings
from raredx.data import phenopackets

app = typer.Typer(help="raredx — rare-disease diagnosis agent.", no_args_is_help=True)
data_app = typer.Typer(help="Datasets: fetch and inspect.", no_args_is_help=True)
app.add_typer(data_app, name="data")

DataDir = Annotated[
    Path, typer.Option(help="Where raw data lives. Defaults to RAREDX_DATA_DIR or ./data.")
]


@data_app.command()
def fetch(data_dir: DataDir = settings.data_dir, force: bool = False) -> None:
    """Download the Phenopacket Store release and verify its checksum."""
    path = phenopackets.fetch(data_dir, force=force)
    typer.echo(f"ok  {path}  (release {phenopackets.RELEASE_VERSION}, sha256 verified)")


@data_app.command()
def stats(data_dir: DataDir = settings.data_dir) -> None:
    """Load every case and summarise what the evaluation set looks like."""
    archive = phenopackets.archive_path(data_dir)
    if not archive.exists():
        raise typer.BadParameter(f"{archive} missing — run `raredx data fetch` first")
    cases, skipped = phenopackets.load(archive)
    n_terms = [len(c.hpo_ids) for c in cases]
    terms = f"{statistics.median(n_terms):.0f} ({min(n_terms)}–{max(n_terms)})"
    split = f"{len(phenopackets.design(cases))} / {len(phenopackets.heldout(cases))}"
    rows = [
        ("cases", len(cases)),
        ("skipped", dict(skipped) or "none"),
        ("with a causal gene", sum(c.gene is not None for c in cases)),
        ("distinct diseases (OMIM)", len({c.disease_id for c in cases})),
        ("distinct genes", len({c.gene for c in cases if c.gene})),
        ("distinct source papers (PMID)", len({c.pmid for c in cases})),
        ("HPO terms per case, median (min–max)", terms),
        ("split design / heldout", split),
    ]
    for label, value in rows:
        typer.echo(f"{label:<40} {value}")

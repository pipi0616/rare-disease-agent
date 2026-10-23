"""The `raredx` command line. Thin: every command calls into the package and prints."""

import functools
import hashlib
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, NoReturn

import typer

from raredx.config import settings
from raredx.data import cases as case_store
from raredx.data import phenopackets, sources
from raredx.data.cases import Case
from raredx.evals import scoring, splits
from raredx.evals.provenance import code_version
from raredx.evals.systems import Oracle, Popularity, System

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI
    from openai import OpenAI

    from raredx.evals.harness import Harness
    from raredx.evals.rag import Question as RagQuestion
    from raredx.knowledge.case_bank import CaseBank
    from raredx.knowledge.corpus import Document
    from raredx.knowledge.diseases import Identity
    from raredx.knowledge.hpo import HPO
    from raredx.llm import Budget
    from raredx.phenotyping.reader import NoteReader, Reader
    from raredx.tools.find_similar_patients import FindSimilarPatients
    from raredx.tools.rank_diseases import RankDiseases
    from raredx.tools.search_disease_texts import SearchDiseaseTexts

app = typer.Typer(help="raredx — rare-disease diagnosis agent.", no_args_is_help=True)
data_app = typer.Typer(help="Datasets: fetch, build and inspect.", no_args_is_help=True)
eval_app = typer.Typer(help="Evaluation: manifests, runs and scores.", no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(eval_app, name="eval")
llm_app = typer.Typer(help="The model endpoint.", no_args_is_help=True)
app.add_typer(llm_app, name="llm")

DATASET = "phenopacket-store"
SNAPSHOT = "phenopacket-store-snapshot"  # the store after the pinned release
RAREBENCH = "rarebench"

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


def _processed(data_dir: Path, evals_dir: Path, name: str = DATASET) -> tuple[Path, list[Case]]:
    """A case source's processed cases: the pinned release unless another is named."""
    out_dir = sources.processed_dir(
        sources.load_sources(evals_dir / "datasets.toml")[name], data_dir
    )
    if not (out_dir / case_store.CASES_FILE).exists():
        build = "raredx data build" + ("" if name == DATASET else f" {name}")
        _fail(f"{out_dir} has no cases yet — run `{build}` first")
    return out_dir, case_store.read(out_dir)


def _dates_file(evals_dir: Path) -> Path:
    return evals_dir / "pubmed_dates.tsv"


# ── data ────────────────────────────────────────────────────────────


@data_app.command()
def fetch(
    names: Annotated[
        list[str] | None, typer.Argument(help="Sources to fetch, as named in the registry.")
    ] = None,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
    force: bool = False,
) -> None:
    """Download registered sources (default: all) into data/raw and verify every checksum."""
    registry = sources.load_sources(evals_dir / "datasets.toml")
    unknown = sorted(set(names or []) - set(registry))
    if unknown:
        _fail(f"not in the registry: {', '.join(unknown)} (registered: {', '.join(registry)})")
    for name in names or registry:
        source = registry[name]
        for path in sources.fetch(source, data_dir, force=force):
            typer.echo(f"ok  {path}  ({source.name} {source.version}, sha256 verified)")


CASE_SOURCES = (DATASET, SNAPSHOT, RAREBENCH)


@data_app.command()
def build(
    name: Annotated[str, typer.Argument(help=" | ".join(CASE_SOURCES))] = DATASET,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Parse a raw download of cases into data/processed: one case per line."""
    if name not in CASE_SOURCES:
        _fail(f"{name} holds no cases: choose {', '.join(CASE_SOURCES)}")
    registry = sources.load_sources(evals_dir / "datasets.toml")
    source = registry[name]
    file = next(iter(source.files))
    raw = sources.raw_dir(source, data_dir) / file
    if not raw.exists():
        _fail(f"{raw} missing — run `raredx data fetch {name}` first")
    info: dict[str, Any] = {"source": source.name, "version": source.version}
    if name == DATASET:
        cases, skipped = phenopackets.load(raw)
    elif name == SNAPSHOT:  # what is new is told apart from the pinned release's papers
        _, release = _processed(data_dir, evals_dir)
        cases, skipped = phenopackets.load(raw, {c.pmid for c in release if c.pmid})
        info["release"] = f"{DATASET} {registry[DATASET].version}"
    else:
        from raredx.data import rarebench

        orphanet = sources.raw_dir(registry["orphanet"], data_dir) / "en_product1.xml"
        if not orphanet.exists():
            _fail("the Orphanet mappings are not downloaded — run `raredx data fetch orphanet`")
        knowledge = _knowledge(evals_dir, data_dir)
        cases, skipped = rarebench.load(raw, knowledge, rarebench.Orphanet(orphanet))
        info["hpo_release"] = knowledge.release
    info |= {"raw_sha256": source.files[file], "cases": len(cases), "skipped": dict(skipped)}
    path = case_store.write(cases, sources.processed_dir(source, data_dir), info)
    typer.echo(f"ok  {path}  ({len(cases)} cases, skipped {dict(skipped) or 'none'})")


@data_app.command()
def index(data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir) -> None:
    """Embed the disease texts (Orphanet, MedlinePlus) for search; a few minutes, once."""
    from raredx.knowledge import texts
    from raredx.knowledge.text_index import FastEmbedder, TextIndex

    registry = sources.load_sources(evals_dir / "datasets.toml")
    folders = {name: sources.raw_dir(registry[name], data_dir) for name in TEXT_SOURCES}
    missing = [name for name, folder in folders.items() if not any(folder.glob("*.xml"))]
    if missing:
        _fail(f"no {', '.join(missing)} download — run `raredx data fetch {' '.join(missing)}`")
    knowledge = _knowledge(evals_dir, data_dir)
    passages = []
    for passage in texts.read(folders["orphanet"], folders["medlineplus"]):
        known = [d for d in passage.disease_ids if d in knowledge.names]
        if known:  # OMIM ids HPO does not know as diseases (e.g. gene entries) are dropped
            passages.append(passage.model_copy(update={"disease_ids": known}))
    typer.echo(f"embedding {len(passages)} passages ...")
    dense, sparse = FastEmbedder(data_dir / "models").passages([p.text for p in passages])
    info = {
        "sources": ", ".join(f"{n} {registry[n].version}" for n in TEXT_SOURCES),
        "hpo_release": knowledge.release,
    }
    folder = _text_index_dir(registry, data_dir, knowledge.release)
    TextIndex.save(folder, passages, dense, sparse, info)
    typer.echo(f"ok  {folder}: {len(passages)} passages")


@data_app.command("hpo-index")
def hpo_index(
    data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir
) -> None:
    """Embed HPO's term names and synonyms, for coding a note's findings; minutes, once."""
    from raredx.knowledge.text_index import FastEmbedder, TextIndex
    from raredx.phenotyping.reader import labels

    knowledge = _knowledge(evals_dir, data_dir)
    names = labels(knowledge)
    typer.echo(f"embedding {len(names)} names and synonyms of {len(knowledge.findings)} terms ...")
    dense, sparse = FastEmbedder(data_dir / "models").passages([n.text for n in names])
    info = {
        "sources": f"HPO {knowledge.release}: names and EXACT/RELATED synonyms of finding terms",
        "hpo_release": knowledge.release,
    }
    folder = _term_index_dir(data_dir, knowledge.release)
    TextIndex.save(folder, names, dense, sparse, info)
    typer.echo(f"ok  {folder}: {len(names)} names and synonyms")


@data_app.command("lirical")
def setup_lirical(
    data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir
) -> None:
    """Set LIRICAL up for comparison runs: unpack the fetched release, let it download
    its gene and transcript data (about 350 MB), put the pinned HPO release in."""
    from raredx.baselines import lirical

    registry = sources.load_sources(evals_dir / "datasets.toml")
    tool, ontology = registry["lirical"], registry["hpo-json"]
    distribution = sources.raw_dir(tool, data_dir) / next(iter(tool.files))
    hp_json = sources.raw_dir(ontology, data_dir) / lirical.ONTOLOGY
    if not distribution.exists() or not hp_json.exists():
        _fail("LIRICAL is not downloaded — run `raredx data fetch lirical hpo-json` first")
    try:
        java = lirical.find_java(settings.java)
    except lirical.JavaNotFound as e:
        _fail(str(e))
    folder = sources.processed_dir(tool, data_dir)
    info = lirical.setup(distribution, hp_json, folder, java)
    typer.echo(
        f"ok  {folder}  (LIRICAL {info['lirical']}, HPO {ontology.version}, "
        f"{info['gene_rows_dropped']} repeated gene rows dropped)"
    )


@data_app.command("deeprare-queries")
def deeprare_queries(
    split: Annotated[list[str], typer.Option(help="Manifests whose cases to prepare.")],
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Embed DeepRare's similar-case query for every case of these manifests, once
    (through OpenRouter, well under a cent), so its runs need no OpenRouter."""
    from raredx import llm
    from raredx.baselines import deeprare

    knowledge = _knowledge(evals_dir, data_dir)
    by_id = {
        c.id: c
        for dataset in {splits.dataset_of(name, DATASET) for name in split}
        for c in _processed(data_dir, evals_dir, dataset)[1]
    }
    texts = [
        deeprare.query_text([knowledge.term(t)[1] for t in by_id[case_id].hpo_ids])
        for name in split
        for case_id, _ in splits.read(_manifest(evals_dir, name))
    ]
    try:
        client = llm.openrouter_client(settings)
    except llm.MissingAPIKey as e:
        _fail(str(e))
    cache = _deeprare_queries(data_dir)
    done = deeprare.embed_queries(texts, cache, client)
    typer.echo(f"ok  {cache}: {done} embedded now, {len(set(texts)) - done} already there")


@data_app.command("pubmed-dates")
def pubmed_dates(
    data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir
) -> None:
    """Look up when each paper the temporal test could draw on was first public (PubMed),
    into evals/pubmed_dates.tsv: the held-out papers, and those the snapshot added."""
    from raredx.data import pubmed

    _, release = _processed(data_dir, evals_dir)
    _, snapshot = _processed(data_dir, evals_dir, SNAPSHOT)
    papers = {c.pmid for c in release if c.split == "heldout" and c.pmid}
    papers |= {c.pmid for c in snapshot if c.split == "external" and c.pmid}
    path = _dates_file(evals_dir)
    added = pubmed.update(path, papers)
    known = pubmed.read(path)
    typer.echo(f"ok  {path}  ({added} looked up now; {len(known)} of {len(papers)} papers dated)")


RAREARENA = "rarearena-rds"
PMC_PMIDS = "pmc_pmids.tsv"


@data_app.command("pmc-ids")
def pmc_ids(
    data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir
) -> None:
    """Map each RareArena report's PMC id to its PMID (NCBI's ID converter), into
    evals/pmc_pmids.tsv, so the report's own paper can be masked."""
    from raredx.data import rarearena

    folder = sources.raw_dir(sources.load_sources(evals_dir / "datasets.toml")[RAREARENA], data_dir)
    if not (folder / rarearena.FILE).exists():
        _fail(f"{folder} has no {rarearena.FILE} — run `raredx data fetch {RAREARENA}` first")
    papers = {r.pmcid for r in rarearena.reports(folder / rarearena.FILE)}
    path = evals_dir / PMC_PMIDS
    added = rarearena.update_pmids(path, papers)
    known = rarearena.read_pmids(path)
    typer.echo(f"ok  {path}  ({added} looked up now; {len(known)} of {len(papers)} papers mapped)")


WIKIPEDIA = "wikipedia"
WIKIPEDIA_REVISIONS = "wikipedia_revisions.tsv"


@data_app.command("wikipedia")
def fetch_wikipedia(
    limit: Annotated[int | None, typer.Option(help="Fetch at most this many now.")] = None,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Wikipedia's articles on the knowledge's diseases: listed from Wikidata and pinned
    by revision into evals/wikipedia_revisions.tsv (once), then fetched as that
    revision's HTML into the raw layer, resuming where a run stopped. No model."""
    from raredx.data import wikipedia

    source = sources.load_sources(evals_dir / "datasets.toml")[WIKIPEDIA]
    manifest = evals_dir / WIKIPEDIA_REVISIONS
    http = wikipedia.client()
    if manifest.exists():
        articles = wikipedia.read_manifest(manifest)
    else:
        knowledge = _knowledge(evals_dir, data_dir, orphanet=True)
        listed = wikipedia.disease_articles(http)
        known = [a for a in listed if any(knowledge.canonical(d) for d in (*a.orpha, *a.omim))]
        articles = wikipedia.with_revisions(known, http)
        wikipedia.write_manifest(manifest, articles)
        typer.echo(f"ok  {manifest}  ({len(listed)} listed, {len(articles)} on known diseases)")
    path = sources.raw_dir(source, data_dir) / wikipedia.PAGES
    done = len(wikipedia.fetched(path))
    for i, _ in enumerate(wikipedia.fetch(articles, path, http), 1):
        if i % 200 == 0:
            typer.echo(f"   {done + i} of {len(articles)} fetched", err=True)
        if limit and i >= limit:
            break
    have = len(wikipedia.fetched(path))
    typer.echo(f"ok  {path}  ({have} of {len(articles)} articles)")


@data_app.command("read-rarearena")
def read_rarearena(
    n: Annotated[int, typer.Option(help="How many reports the sample holds.")] = 500,
    limit: Annotated[
        int | None, typer.Option(help="Read at most this many reports now; the rest later.")
    ] = None,
    budget_usd: Annotated[float, typer.Option(help="Stop calling the model past this.")] = 3.0,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Sample RareArena reports by fixed rules (data.rarearena.sample), read each into HPO
    terms with the note reader, and write them as development cases; once all are read,
    the manifest rarearena-dev. Resumes: a report already read is not read again."""
    import json

    from raredx import llm
    from raredx.data import rarearena
    from raredx.knowledge import prevalence
    from raredx.phenotyping.reader import terms

    source = sources.load_sources(evals_dir / "datasets.toml")[RAREARENA]
    raw = sources.raw_dir(source, data_dir) / rarearena.FILE
    if not raw.exists():
        _fail(f"{raw} missing — run `raredx data fetch {RAREARENA}` first")
    pmids = rarearena.read_pmids(evals_dir / PMC_PMIDS)
    if not pmids:
        _fail("no PMC-to-PMID table — run `raredx data pmc-ids` first")
    merged = _knowledge(evals_dir, data_dir, orphanet=True)
    _, release = _processed(data_dir, evals_dir)
    _, snapshot = _processed(data_dir, evals_dir, SNAPSHOT)
    store_papers = {c.pmid for c in release + snapshot if c.pmid}
    candidates = [
        r
        for r in rarearena.reports(raw)
        if r.pmcid in pmids
        and pmids[r.pmcid] not in store_papers
        and merged.canonical(r.disease_id) is not None
    ]
    files = _orphanet_prevalence_files(evals_dir, data_dir)
    band = prevalence.disease_bands(*files, _identity(evals_dir, data_dir).same)
    chosen = rarearena.sample(candidates, pmids, dict(band), n)

    out_dir = sources.processed_dir(source, data_dir)
    readings_file = out_dir / "readings.jsonl"
    done: dict[str, list[dict[str, Any]]] = {}
    if readings_file.exists():
        for line in readings_file.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            done[record["id"]] = record["findings"]
    reader = _note_reader(evals_dir, data_dir, llm.Budget(budget_usd, _prices()))
    tally = llm.Tally()
    to_read = [r for r in chosen if r.id not in done][:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    with readings_file.open("a", encoding="utf-8") as f:
        for i, report in enumerate(to_read, 1):
            findings = reader.read(report.text, tally)
            done[report.id] = [x.model_dump() for x in findings]
            f.write(json.dumps({"id": report.id, "findings": done[report.id]}) + "\n")
            f.flush()
            if i % 25 == 0:
                typer.echo(f"  read {i} of {len(to_read)}  (about ${tally.cost(settings):.3f})")

    from raredx.phenotyping.reader import Finding

    cases, unreadable = [], []
    for report in chosen:
        if report.id not in done:
            continue
        present = terms([Finding.model_validate(x) for x in done[report.id]])
        if not present:
            unreadable.append(report.id)
            continue
        cases.append(
            Case(
                id=report.id,
                cohort="rarearena",
                hpo_ids=present,
                hpo_labels=[merged.term(t)[1] for t in present],
                disease_id=report.disease_id,
                disease_label=report.disease_label,
                gene=None,
                variants=[],
                pmid=pmids[report.pmcid],
                sex=report.sex,
                split="external",
            )
        )
    build = {
        "source": RAREARENA,
        "version": source.version,
        "raw_sha256": source.files[rarearena.FILE],
        "reader": reader.config(),
        "sample": {"n": n, "seed": rarearena.SEED, "per_disease": rarearena.PER_DISEASE},
        "read": len(done),
        "unreadable": unreadable,
    }
    case_store.write(cases, out_dir, build)
    cost = f"about ${tally.cost(settings):.4f} for {len(to_read)} reports read now"
    typer.echo(f"ok  {out_dir}  ({len(cases)} cases; {len(unreadable)} with no finding; {cost})")
    if all(r.id in done for r in chosen):
        manifest = evals_dir / "splits" / f"{splits.RAREARENA}.tsv"
        rows = sorted((c.id, c.pmid or "") for c in cases)
        text = splits.render(rows)
        if manifest.exists() and manifest.read_text(encoding="utf-8") != text:
            _fail(f"{manifest} exists and differs: a manifest is frozen")
        manifest.write_text(text, encoding="utf-8")
        typer.echo(f"ok  {manifest}  ({len(rows)} cases)")


def _prices() -> tuple[float, float, float]:
    return (settings.llm_price_input, settings.llm_price_cached_input, settings.llm_price_output)


CASE_INDEX = "case_index"


def _case_index_dir(evals_dir: Path, data_dir: Path) -> Path:
    source = sources.load_sources(evals_dir / "datasets.toml")[RAREARENA]
    return sources.processed_dir(source, data_dir) / CASE_INDEX


@data_app.command("case-index")
def case_index(
    data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir
) -> None:
    """Index RareArena's case reports for the similar-reports route: dense and BM25
    vectors computed on this machine (about twenty minutes, once). No model is called."""
    from raredx.data import rarearena
    from raredx.knowledge import case_bank
    from raredx.knowledge.text_index import FastEmbedder

    source = sources.load_sources(evals_dir / "datasets.toml")[RAREARENA]
    raw = sources.raw_dir(source, data_dir) / rarearena.FILE
    pmids = rarearena.read_pmids(evals_dir / PMC_PMIDS)
    if not raw.exists() or not pmids:
        _fail(f"needs {raw} and evals/{PMC_PMIDS}: run `raredx data fetch {RAREARENA}`, `pmc-ids`")
    folder = _case_index_dir(evals_dir, data_dir)
    n = case_bank.build(raw, pmids, FastEmbedder(data_dir / "models"), folder)
    typer.echo(f"ok  {folder}  ({n} reports indexed)")


def _case_bank(evals_dir: Path, data_dir: Path) -> "CaseBank":
    from raredx.knowledge.case_bank import CaseBank, Report
    from raredx.knowledge.text_index import INFO, FastEmbedder, TextIndex

    folder = _case_index_dir(evals_dir, data_dir)
    if not (folder / INFO).exists():
        _fail(f"{folder} has no case index — run `raredx data case-index` first")
    return CaseBank(TextIndex.load(folder, FastEmbedder(data_dir / "models"), Report))


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
    external: Annotated[
        bool, typer.Option(help="The temporal and RareBench manifests, from their datasets.")
    ] = False,
    force: bool = False,
) -> None:
    """Create the manifests in evals/splits, or confirm they are unchanged. With
    --external, the four that test v1.0 on cases from outside the pinned release."""
    try:
        if external:
            from raredx.data import pubmed

            _, snapshot = _processed(data_dir, evals_dir, SNAPSHOT)
            _, rarebench = _processed(data_dir, evals_dir, RAREBENCH)
            dates = pubmed.read(_dates_file(evals_dir))
            if not dates:
                _fail("no publication dates — run `raredx data pubmed-dates` first")
            status = splits.make_external(
                snapshot, rarebench, dates, evals_dir / "splits", force=force
            )
        else:
            _, cases = _processed(data_dir, evals_dir)
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
    from raredx.data import pubmed

    folder = splits_dir or evals_dir / "splits"
    dates = pubmed.read(_dates_file(evals_dir))
    problems = splits.check(folder) + splits.check_external(folder, dates or None)
    problems += splits.check_development(folder)
    registry = sources.load_sources(evals_dir / "datasets.toml")
    out_dir = sources.processed_dir(registry[DATASET], data_dir)
    if not problems and (out_dir / case_store.CASES_FILE).exists():
        problems = splits.check_against(case_store.read(out_dir), folder)
    others = [sources.processed_dir(registry[n], data_dir) for n in (SNAPSHOT, RAREBENCH)]
    external = [n for n in splits.EXTERNAL if (folder / f"{n}.tsv").exists()]
    if not problems and external and all((d / case_store.CASES_FILE).exists() for d in others):
        snapshot, rarebench = (case_store.read(d) for d in others)
        problems = splits.check_external_against(snapshot, rarebench, dates, folder)
    for problem in problems:
        typer.echo(f"problem  {problem}")
    if problems:
        raise typer.Exit(1)
    development = [n for n in splits.DEVELOPMENT if (folder / f"{n}.tsv").exists()]
    names = [*splits.NAMES, *external, *development]
    typer.echo(f"ok  {folder}: {', '.join(names)} pass every rule")


SYSTEMS = (
    "oracle",
    "popularity",
    "phenotype-rank",
    "rank-then-check",
    "similar-patients",
    "disease-texts",
    "gene-rank",
    "lirical",
    "deeprare",
    "fixed-pipeline",
    "agent",
    "seeded-agent",
    "hypothesis-agent",
    "llm-direct",
    "llm-direct-thinking",
    "judge-table",
    "judge-review",
    "judge-table-thinking",
    "judge-review-thinking",
)


def _mondo_version(evals_dir: Path) -> str:
    return sources.load_sources(evals_dir / "datasets.toml")["mondo"].version


@functools.cache
def _identity(evals_dir: Path, data_dir: Path) -> "Identity":
    """Disease identity across OMIM and Orphanet: the pinned Mondo mappings."""
    from raredx.knowledge.diseases import MAPPINGS, Identity

    folder = sources.raw_dir(sources.load_sources(evals_dir / "datasets.toml")["mondo"], data_dir)
    if not (folder / MAPPINGS).exists():
        _fail(f"{folder} has no Mondo mappings — run `raredx data fetch mondo` first")
    return Identity(folder / MAPPINGS)


@functools.cache  # one release per process (hpo3 holds one ontology); load it once
def _knowledge(evals_dir: Path, data_dir: Path, orphanet: bool | None = None) -> "HPO":
    """The pinned HPO release, loaded; with Orphanet's annotations merged in by disease
    identity when asked or set (settings.orphanet, chapter 31); a clear message if it was
    never fetched."""
    from raredx.knowledge import hpo

    folder = sources.raw_dir(sources.load_sources(evals_dir / "datasets.toml")["hpo"], data_dir)
    if not (folder / "hp.obo").exists():
        _fail(f"{folder} has no HPO release — run `raredx data fetch hpo` first")
    merged = settings.orphanet if orphanet is None else orphanet
    return hpo.load(folder, _identity(evals_dir, data_dir) if merged else None)


def _knowledge_label(evals_dir: Path) -> str:
    """Which knowledge a run read, as recorded with it."""
    if settings.orphanet:
        return f"HPO OMIM + Orphanet, merged by mondo {_mondo_version(evals_dir)}"
    return "HPO OMIM"


def _ranker(evals_dir: Path, data_dir: Path, similarity: str | None) -> "RankDiseases":
    """Tool T2 on the pinned HPO release, with the default similarity unless one is given."""
    from raredx.tools.rank_diseases import RankDiseases

    knowledge = _knowledge(evals_dir, data_dir)
    try:
        if similarity is None:
            return RankDiseases(knowledge)
        method, _, combine = similarity.partition("/")
        return RankDiseases(knowledge, method, combine)
    except ValueError as e:
        _fail(str(e))


def _patient_bank(
    cases: list[Case],
    evals_dir: Path,
    data_dir: Path,
    *,
    splits_used: tuple[str, ...] = ("design",),
) -> "FindSimilarPatients":
    """Tool T5 over the published patients of the given splits. Evaluation uses the
    design split alone: the heldout cases stay unseen until the final run."""
    from raredx.tools.find_similar_patients import FindSimilarPatients

    build = case_store.read_build_info(sources.processed_dir(_source(evals_dir), data_dir))
    bank = [c for c in cases if c.split in splits_used]
    name = f"{build['source']} {build['version']}, {' + '.join(splits_used)}: {len(bank)} patients"
    return FindSimilarPatients(_knowledge(evals_dir, data_dir), bank, name)


TEXT_SOURCES = ("orphanet", "medlineplus")


def _text_index_dir(
    registry: dict[str, "sources.Source"], data_dir: Path, hpo_release: str
) -> Path:
    versions = "_".join(f"{n}-{registry[n].version}" for n in TEXT_SOURCES)
    return data_dir / "processed" / "disease-texts" / f"{versions}_hpo-{hpo_release}"


def _text_search(evals_dir: Path, data_dir: Path) -> "SearchDiseaseTexts":
    """Tool T6 over the embedded disease texts; a clear message if they were never built."""
    from raredx.knowledge.text_index import INFO, FastEmbedder, TextIndex
    from raredx.knowledge.texts import Passage
    from raredx.tools.search_disease_texts import SearchDiseaseTexts

    knowledge = _knowledge(evals_dir, data_dir)
    registry = sources.load_sources(evals_dir / "datasets.toml")
    folder = _text_index_dir(registry, data_dir, knowledge.release)
    if not (folder / INFO).exists():
        _fail(f"{folder} has no text index — run `raredx data index` first")
    index = TextIndex.load(folder, FastEmbedder(data_dir / "models"), Passage)
    return SearchDiseaseTexts(index, knowledge)


OPENROUTER = "openrouter:"


def _orphanet_prevalence_files(evals_dir: Path, data_dir: Path) -> tuple[Path, Path]:
    """Orphanet's prevalence file and its disorder file (for the mapping to OMIM)."""
    from raredx.knowledge import prevalence

    registry = sources.load_sources(evals_dir / "datasets.toml")
    folders = {name: sources.raw_dir(registry[name], data_dir) for name in ORPHANET_SOURCES}
    files = (
        folders["orphanet-prevalence"] / prevalence.PREVALENCE,
        folders["orphanet"] / "en_product1.xml",
    )
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        _fail(f"no Orphanet prevalence: {', '.join(missing)} — run `raredx data fetch` first")
    return files


def _prevalence(evals_dir: Path, data_dir: Path) -> dict[str, str]:
    """Each disease's Orphanet prevalence class (OMIM ids through disease identity), for
    the hypothesis agent."""
    from raredx.knowledge import prevalence

    files = _orphanet_prevalence_files(evals_dir, data_dir)
    return prevalence.disease_classes(*files, _identity(evals_dir, data_dir).same)


def _deeprare_queries(data_dir: Path) -> Path:
    from raredx.baselines.deeprare import QUERY_EMBEDDINGS

    return data_dir / "processed" / "deeprare" / QUERY_EMBEDDINGS


# Tools an agent can be given beyond the four core ones; --without leaves one out.
EXTRA_TOOLS = ("find_similar_patients", "search_disease_texts", "rank_candidate_genes")
AGENTS = ("agent", "seeded-agent", "hypothesis-agent")
ORPHANET_SOURCES = ("orphanet-prevalence", "orphanet")


def _model_client() -> "OpenAI":
    from raredx import llm

    try:
        return llm.client(settings)
    except llm.MissingAPIKey as e:
        _fail(str(e))


def _system(
    name: str,
    cases: list[Case],
    evals_dir: Path,
    data_dir: Path,
    similarity: str | None = None,
    without: tuple[str, ...] = (),
    with_genes: bool = False,
    from_run: str | None = None,
    with_texts: bool = False,
    llm_model: str | None = None,
    budget_usd: float | None = None,
    asked: list[Case] | None = None,
) -> System:
    if llm_model and name not in ("llm-direct", "llm-direct-thinking"):
        _fail("--model applies to llm-direct only")
    if name == "oracle":
        return Oracle.from_cases(asked or cases)
    if name == "popularity":
        dev_papers = {pmid for _, pmid in splits.read(evals_dir / "splits" / "dev-200.tsv")}
        pool = [c for c in cases if c.split == "design" and c.pmid not in dev_papers]
        return Popularity.from_cases(pool)
    if name == "phenotype-rank":
        from raredx.baselines.phenotype_rank import PhenotypeRank

        return PhenotypeRank(_ranker(evals_dir, data_dir, similarity))
    if name == "rank-then-check":
        from raredx.baselines.rank_then_check import RankThenCheck
        from raredx.tools.check_match import CheckMatch

        ranker = _ranker(evals_dir, data_dir, similarity)
        return RankThenCheck(ranker, CheckMatch(ranker.hpo))
    if name == "similar-patients":
        from raredx.baselines.similar_patients import SimilarPatientsRank

        return SimilarPatientsRank(_patient_bank(cases, evals_dir, data_dir))
    if name == "disease-texts":
        from raredx.baselines.disease_texts import DiseaseTextsRank

        return DiseaseTextsRank(_text_search(evals_dir, data_dir))
    if name == "gene-rank":
        from raredx.baselines.gene_rank import GeneRank
        from raredx.tools.rank_candidate_genes import RankCandidateGenes

        if not with_genes:
            _fail("gene-rank ranks candidate genes: run it with --with-genes")
        return GeneRank(RankCandidateGenes(_knowledge(evals_dir, data_dir)))
    if name == "lirical":
        from raredx.baselines import lirical

        registry = sources.load_sources(evals_dir / "datasets.toml")
        folder = sources.processed_dir(registry["lirical"], data_dir)
        knowledge = _knowledge(evals_dir, data_dir)
        try:
            return lirical.Lirical(knowledge, folder, lirical.find_java(settings.java))
        except (lirical.LiricalNotSetUp, lirical.JavaNotFound) as e:
            _fail(str(e))
    if name == "deeprare":
        from raredx.baselines.deeprare import DeepRare, DeepRareNotSetUp

        def secret(value: Any) -> str:
            return str(value.get_secret_value()) if value is not None else ""

        keys = {
            "DEEPSEEK_API_KEY": secret(settings.llm_api_key),
            "OPENROUTER_API_KEY": secret(settings.openrouter_api_key),
        }
        try:
            return DeepRare(
                _knowledge(evals_dir, data_dir),
                settings.deeprare_dir,
                keys,
                _deeprare_queries(data_dir),
                _deeprare_queries(data_dir).parent / "answers",
            )
        except DeepRareNotSetUp as e:
            _fail(str(e))
    if name == "fixed-pipeline":
        from raredx.baselines.fixed_pipeline import FixedPipeline
        from raredx.tools.check_match import CheckMatch
        from raredx.tools.lookup_disease import LookupDisease

        ranker = _ranker(evals_dir, data_dir, similarity)
        return FixedPipeline(
            _model_client(),
            settings.llm_model,
            ranker,
            CheckMatch(ranker.hpo),
            LookupDisease(ranker.hpo),
        )
    if name in AGENTS:
        from raredx import llm
        from raredx.agent import Agent

        knowledge = _knowledge(evals_dir, data_dir)
        try:
            model = llm.chat_model(settings)
        except llm.MissingAPIKey as e:
            _fail(str(e))
        extra: list[Any] = []
        if "find_similar_patients" not in without:
            extra.append(_patient_bank(cases, evals_dir, data_dir))
        # Off by default since chapter 20: on dev-200 the text search added nothing (4 cases
        # to 2 at top-1, p = 0.69) and cost 18% more tokens. --with-texts adds it back. On
        # by default for the hypothesis agent: the diseases HPO annotates thinly, which the
        # model may name itself, are what the texts describe.
        texts = with_texts or name == "hypothesis-agent"
        if texts and "search_disease_texts" not in without:
            extra.append(_text_search(evals_dir, data_dir))
        if with_genes and "rank_candidate_genes" not in without:
            from raredx.tools.rank_candidate_genes import RankCandidateGenes

            extra.append(RankCandidateGenes(knowledge))
        label = name
        if with_texts and name != "hypothesis-agent":
            label += " (with search_disease_texts)"
        if without:
            label += f" (without {', '.join(without)})"
        return Agent(
            model,
            settings.llm_model,
            knowledge,
            seeded=name == "seeded-agent",
            hypotheses=name == "hypothesis-agent",
            prevalence=_prevalence(evals_dir, data_dir) if name == "hypothesis-agent" else None,
            extra_tools=extra,
            name=label,
        )
    if name.startswith("judge-"):
        from raredx.evals.evidence import gather
        from raredx.evals.harness import candidates_of
        from raredx.judge import EvidenceJudge

        if not from_run:
            _fail("the judge replays a recorded agent run: give --from-run RUN_ID")
        variant, _, thinking = name.removeprefix("judge-").partition("-")
        traces = _harness().answers(from_run)
        evidence = {e.case_id: e for e in map(gather, traces)}
        answers = {
            t.data.spans[0].inputs["question"]["case_id"]: candidates_of(t.data.spans[0].outputs)
            for t in traces
        }
        return EvidenceJudge(
            _model_client(),
            settings.llm_model,
            evidence,
            answers,
            from_run,
            variant,
            thinking=thinking == "thinking",
        )
    if name in ("llm-direct", "llm-direct-thinking"):
        from raredx import llm
        from raredx.baselines.llm_direct import LLMDirect

        reasoning = name == "llm-direct-thinking"
        if llm_model is None:
            return LLMDirect(_model_client(), settings.llm_model, thinking=reasoning)
        if not llm_model.startswith(OPENROUTER):
            _fail(f"--model takes an OpenRouter model id, written {OPENROUTER}provider/model")
        if budget_usd is None:
            _fail("a run billed through OpenRouter needs a cap: give --budget-usd")
        try:
            client = llm.openrouter_client(settings)
        except llm.MissingAPIKey as e:
            _fail(str(e))
        return LLMDirect(
            client,
            llm_model.removeprefix(OPENROUTER),
            thinking=reasoning,
            provider="openrouter",
            budget=llm.Budget(budget_usd),
        )
    _fail(f"unknown system {name!r}: choose {', '.join(SYSTEMS)}")


def _hidden_of(evals_dir: Path, data_dir: Path) -> "Callable[[str], set[str]] | None":
    """For the leak audit: the diseases HPO knows only from a given paper. None when the
    HPO release was never fetched (then only the paper itself is looked for)."""
    folder = sources.raw_dir(sources.load_sources(evals_dir / "datasets.toml")["hpo"], data_dir)
    if not (folder / "hp.obo").exists():
        return None
    knowledge = _knowledge(evals_dir, data_dir)
    return lambda pmid: knowledge.known_only_from(frozenset({pmid}))


def _harness(identity: "Identity | None" = None) -> "Harness":
    """The evaluation harness; given disease identity, its scorer counts an answer naming
    any id equal to the confirmed one (it scores; reading recorded runs needs none)."""
    from raredx.evals.harness import Harness  # imported here: mlflow is slow to load

    same = identity.same if identity is not None else None
    return Harness(settings.mlflow_tracking_uri, settings.mlflow_artifact_root, same)


def _manifest(evals_dir: Path, split: str) -> Path:
    manifest = evals_dir / "splits" / f"{split}.tsv"
    if not manifest.exists():
        _fail(f"{manifest} not found")
    return manifest


@eval_app.command("run")
def run_system(
    system: Annotated[str, typer.Option(help=" | ".join(SYSTEMS))],
    split: Annotated[str, typer.Option(help="Manifest to run on.")] = "dev-200",
    final: Annotated[bool, typer.Option(help="Required for heldout: the final run.")] = False,
    orphanet: Annotated[
        bool,
        typer.Option(help="Read Orphanet's annotations too, merged in by disease identity."),
    ] = settings.orphanet,
    similarity: Annotated[
        str | None,
        typer.Option(help="The phenotype systems: hpo3 method/combination, e.g. lin/funSimAvg."),
    ] = None,
    mask_source_paper: Annotated[
        bool,
        typer.Option(help="Hide each case's source paper from the knowledge tools read."),
    ] = True,
    without: Annotated[
        list[str] | None,
        typer.Option(help=f"The agents: leave out a tool ({' | '.join(EXTRA_TOOLS)}); repeatable."),
    ] = None,
    with_genes: Annotated[
        bool,
        typer.Option(help="The genotype track: each case comes with simulated candidate genes."),
    ] = False,
    from_run: Annotated[
        str | None,
        typer.Option(help="The judges: the recorded agent run whose evidence they rule on."),
    ] = None,
    with_texts: Annotated[
        bool,
        typer.Option(help="The agents: add the disease-text search, off by default since ch 20."),
    ] = False,
    model: Annotated[
        str | None,
        typer.Option(
            help="llm-direct: another provider's model through OpenRouter, "
            "e.g. openrouter:anthropic/claude-sonnet-5.5"
        ),
    ] = None,
    budget_usd: Annotated[
        float | None,
        typer.Option(help="OpenRouter runs: stop calling the model once this much is spent."),
    ] = None,
    fill_in: Annotated[
        str | None,
        typer.Option(
            help="A run of the same system on the same manifest: ask again only the cases "
            "it lost to a model-API failure, as a run that completes it."
        ),
    ] = None,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Evaluate a system on a manifest with MLflow; the run and every answer are recorded."""
    settings.orphanet = orphanet  # before any knowledge is loaded in this process
    if split.startswith("heldout") and not final:
        _fail("heldout is the final exam: run it once, with --final, when the design is frozen")
    if split in splits.EXTERNAL and split not in splits.PRACTICE and not final:
        _fail(f"{split} tests the frozen system again: run it once, with --final")
    left_out = tuple(sorted(set(without or [])))
    unknown = [t for t in left_out if t not in EXTRA_TOOLS]
    if unknown:
        _fail(f"--without takes {', '.join(EXTRA_TOOLS)}; not {', '.join(unknown)}")
    if left_out and system not in AGENTS:
        _fail("--without applies to the agents only")
    if model and system not in ("llm-direct", "llm-direct-thinking"):
        _fail("--model applies to llm-direct only")
    if model and budget_usd is None:
        _fail("a run billed through OpenRouter needs a cap: give --budget-usd")
    # The systems are built on the pinned release (its design half fills the patient
    # bank) whatever the manifest; an external manifest's cases come from its own dataset.
    _, cases = _processed(data_dir, evals_dir)
    out_dir, asked = _processed(data_dir, evals_dir, splits.dataset_of(split, DATASET))
    manifest = _manifest(evals_dir, split)
    by_id = {c.id: c for c in asked}
    selected = [by_id[case_id] for case_id, _ in splits.read(manifest)]
    lost: dict[str, str] = {}
    if fill_in:
        earlier = _harness().client.get_run(fill_in).data.params
        if earlier.get("manifest") != split:
            _fail(f"run {fill_in} was not made on {split}")
        lost = _harness().lost_cases(fill_in)
        if not lost:
            _fail(f"run {fill_in} lost no case to the model API: there is nothing to fill in")
        selected = [c for c in selected if c.id in lost]
    chosen = _system(
        system,
        cases,
        evals_dir,
        data_dir,
        similarity,
        left_out,
        with_genes,
        from_run,
        with_texts,
        model,
        budget_usd,
        selected,
    )
    billed = getattr(chosen, "provider", None) == "openrouter"
    recorded = getattr(chosen, "evidence", None)
    if isinstance(recorded, dict) and {c.id for c in selected} - set(recorded):
        _fail(f"run {from_run} has no record of some cases in {split}: replay the same manifest")
    build = case_store.read_build_info(out_dir)
    manifest_sha256 = sources.sha256_of(manifest)
    params = {
        "system": chosen.name,
        "manifest": split,
        "manifest_sha256": manifest_sha256,
        "dataset": f"{build['source']} {build['version']}",
        "dataset_sha256": build["raw_sha256"],
        "code": code_version(),
        # Scored by ids, any id Mondo makes equal to the confirmed one counting (chapter 31).
        "disease_identity": f"mondo {_mondo_version(evals_dir)}",
        "knowledge": _knowledge_label(evals_dir),
    }
    system_params = getattr(chosen, "params", None)
    if callable(system_params):  # e.g. the model, thinking mode and prompt version
        params.update(system_params())
    if fill_in:
        if _harness().client.get_run(fill_in).data.params.get("system") != chosen.name:
            _fail(f"run {fill_in} was made by another system")
        params |= {"fills_in": fill_in, "cases_asked_again": len(selected)}
    label, dataset_sha256, genes = split, manifest_sha256, None
    if with_genes:  # its own experiment and dataset: a different exam
        from raredx.evals import candidates

        knowledge = _knowledge(evals_dir, data_dir)
        without_gene = [c.id for c in selected if c.gene is None]
        selected = [c for c in selected if c.gene is not None]  # nothing to sequence otherwise
        if not selected:
            _fail(f"no case in {split} has a causal gene: there is nothing to sequence")
        genes = {c.id: candidates.candidate_genes(c, knowledge) for c in selected}
        params["cases_without_a_causal_gene_left_out"] = len(without_gene)
        label = f"{split}+genes"
        dataset_sha256 = hashlib.sha256(f"{manifest_sha256} {candidates.SPEC}".encode()).hexdigest()
        params |= {"label": label, "track": "phenotype+genes", "candidates": candidates.SPEC}
    from raredx.evals.harness import IncompleteRun

    harness = _harness(_identity(evals_dir, data_dir))
    try:
        run_id, summary = harness.evaluate(
            chosen,
            label,
            dataset_sha256,
            selected,
            params,
            mask_source_papers=mask_source_paper,
            hidden_of=_hidden_of(evals_dir, data_dir),
            genes=genes,
            part=bool(fill_in),
        )
    except IncompleteRun as e:
        _fail(str(e))
    usage = harness.usage(run_id)
    tokens_in, tokens_out = usage["usage/input_tokens"], usage["usage/output_tokens"]
    cached = usage["usage/cached_input_tokens"]
    if billed:  # what OpenRouter said each call cost, summed; not an estimate
        usage["usage/cost_usd_billed"] = round(chosen.budget.spent, 4)  # type: ignore[attr-defined]
        harness.log_metrics(run_id, usage)
    elif tokens_in or tokens_out:
        cost = (
            (tokens_in - cached) * settings.llm_price_input
            + cached * settings.llm_price_cached_input
            + tokens_out * settings.llm_price_output
        ) / 1e6
        usage["usage/cost_usd_estimate"] = round(cost, 4)
        harness.log_metrics(run_id, usage)
    unmasked = "" if mask_source_paper else " · unmasked"
    typer.echo(scoring.render(summary, f"{chosen.name} · {label}{unmasked}"))
    if summary.n_answered < summary.n_cases:
        missing = summary.n_cases - summary.n_answered
        typer.echo(f"note: {missing} cases got no answer; their traces in MLflow show why")
    if billed:
        typer.echo(
            f"usage: {tokens_in:,.0f} input + {tokens_out:,.0f} output tokens, "
            f"${usage['usage/cost_usd_billed']:.4f} billed by OpenRouter; "
            f"{usage['usage/seconds_per_case']:.1f} s per case"
        )
    elif tokens_in or tokens_out:
        typer.echo(
            f"usage: {tokens_in:,.0f} input ({cached:,.0f} cached) + {tokens_out:,.0f} output "
            f"tokens, about ${usage['usage/cost_usd_estimate']:.2f} at peak price; "
            f"{usage['usage/seconds_per_case']:.1f} s per case"
        )
    typer.echo(f"recorded in MLflow: experiment eval/{label}, run {run_id}")
    run_data = harness.client.get_run(run_id).data
    if run_data.metrics.get("errors/model_api"):
        _fail(
            f"{run_data.metrics['errors/model_api']:.0f} cases failed because the model API "
            f"failed ({run_data.tags.get('model_api_errors', '')}): these numbers are not the "
            "system's — fix the cause and run again"
        )
    if mask_source_paper:
        run = harness.client.get_run(run_id).data
        audit = (
            f"{run.metrics['leak/tool_outputs_read']:,.0f} tool outputs read; "
            f"own paper shown {run.metrics['leak/own_paper_shown']:.0f}, "
            f"diseases known only from it shown {run.metrics['leak/hidden_disease_shown']:.0f}"
        )
        if run.tags["leak_audit"] == "failed":
            _fail(f"leak audit FAILED ({audit}): do not use these numbers")
        if run.tags["leak_audit"] == "no tool outputs":
            typer.echo("leak audit: no tool outputs to read (the system calls no tools)")
        else:
            typer.echo(f"leak audit passed: {audit}")


@eval_app.command("score")
def score_run(
    run_id: Annotated[str, typer.Argument(help="An MLflow run id, from `raredx eval runs`.")],
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Score a recorded run again from its traces, as a new run. Nothing is re-asked.
    Scored as runs are scored now: any id Mondo makes equal to the confirmed one counts."""
    harness = _harness(_identity(evals_dir, data_dir))
    params = dict(harness.client.get_run(run_id).data.params)
    manifest = _manifest(evals_dir, params["manifest"])
    from raredx.evals.harness import IncompleteRun, ManifestMismatch

    expected = len(splits.read(manifest)) - int(
        params.get("cases_without_a_causal_gene_left_out", 0)
    )
    try:
        new_id, summary, _ = harness.rescore(run_id, sources.sha256_of(manifest), expected)
    except (ManifestMismatch, IncompleteRun) as e:
        _fail(str(e))
    harness.client.log_param(new_id, "disease_identity", f"mondo {_mondo_version(evals_dir)}")
    typer.echo(scoring.render(summary, f"{params['system']} · {params['manifest']} · rescored"))
    label = params.get("label", params["manifest"])
    typer.echo(f"recorded in MLflow: experiment eval/{label}, run {new_id}")


@eval_app.command("compare")
def compare_runs(
    run_a: Annotated[str, typer.Argument(help="An MLflow run id, from `raredx eval runs`.")],
    run_b: Annotated[str, typer.Argument(help="Another run on the same manifest.")],
    k: Annotated[int, typer.Option(help="Compare on top-k: 1, 3, 5 or 10.")] = 1,
) -> None:
    """Compare two runs question by question: which cases each got that the other missed."""
    if k not in scoring.KS:
        _fail(f"k must be one of {', '.join(map(str, scoring.KS))}")
    from mlflow.exceptions import MlflowException

    harness = _harness()
    try:
        a, b = harness.client.get_run(run_a), harness.client.get_run(run_b)
    except MlflowException:
        _fail("no such run — copy run ids from `raredx eval runs`")
    if a.data.params.get("manifest_sha256") != b.data.params.get("manifest_sha256"):
        _fail("the two runs were not made on the same manifest; there is nothing to pair")
    hits_a, hits_b = harness.hits(run_a, k), harness.hits(run_b, k)
    if set(hits_a) != set(hits_b):
        _fail("the two runs recorded different cases")
    name_a, name_b = a.info.run_name, b.info.run_name
    only_a = sum(hits_a[c] and not hits_b[c] for c in hits_a)
    only_b = sum(hits_b[c] and not hits_a[c] for c in hits_a)
    both = sum(hits_a[c] and hits_b[c] for c in hits_a)
    typer.echo(f"{a.data.params['manifest']} · top-{k} · {len(hits_a)} cases, paired")
    typer.echo(f"  only {name_a} ({run_a[:8]}) right: {only_a:>4}")
    typer.echo(f"  only {name_b} ({run_b[:8]}) right: {only_b:>4}")
    typer.echo(f"  both right: {both}   neither: {len(hits_a) - both - only_a - only_b}")
    typer.echo(f"  sign test, two-sided: {scoring.p_value(scoring.sign_test(only_a, only_b))}")


@eval_app.command("hits")
def hits_table(
    split: Annotated[str, typer.Option(help="The manifest whose cases make the rows.")],
    run: Annotated[
        list[str],
        typer.Option(
            help="NAME=RUN_ID, a column per run in this order; repeatable. NAME=RUN_ID+FILL_ID: "
            "a run completed by the run that asked again the cases it lost (--fill-in)."
        ),
    ],
    out: Annotated[Path, typer.Option(help="The table to write (TSV).")],
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Write each case's verdict under several runs, side by side, for paired comparisons.
    A run that failed its leak audit, or lost cases to the model API that no later run
    answered, is refused."""
    from mlflow.exceptions import MlflowException

    from raredx.evals import hits

    _, pool = _processed(data_dir, evals_dir, splits.dataset_of(split, DATASET))
    by_id = {c.id: c for c in pool}
    cases = [by_id[case_id] for case_id, _ in splits.read(_manifest(evals_dir, split))]
    harness = _harness()
    columns = {}
    for item in run:
        name, _, chain = item.partition("=")
        parts = []
        for run_id in chain.split("+"):
            try:
                recorded = harness.client.get_run(run_id)
            except MlflowException:
                _fail(f"{name}: no such run {run_id!r}")
            if recorded.info.status != "FINISHED":
                _fail(f"{name}: run {run_id} did not finish: it is void")
            if recorded.data.tags.get("leak_audit") == "failed":
                _fail(f"{name}: run {run_id} failed its leak audit")
            got = {k: harness.hits(run_id, k) for k in scoring.KS}
            parts.append((got, set(harness.lost_cases(run_id))))
        verdicts, lost = hits.combine(parts)
        if lost & {c.id for c in cases}:
            _fail(f"{name}: {len(lost)} cases were lost to the model API and never asked again")
        columns[name] = verdicts
    try:
        rows = hits.table(cases, columns, _knowledge(evals_dir, data_dir))
    except ValueError as e:
        _fail(str(e))
    hits.write(rows, out)
    answerable = sum(r["answerable"] == "1" for r in rows)
    typer.echo(f"ok  {out}  ({len(rows)} cases, {answerable} answerable; {', '.join(columns)})")


CALIBRATION = "calibration.toml"
CALIBRATED = ("model", "v1.0", "v1.1")  # the recorded runs read per source


def _show_pool(case: Case, rows: list[Any], names: dict[str, str]) -> None:
    """One case's pool as a table: where each route put a candidate, and its evidence."""
    import math

    def place(value: float) -> str:  # a route's feature is 1 / the place; 0 if not named
        return str(round(1 / value)) if value else "-"

    def count(value: float) -> str:  # counts are kept as log(1 + n)
        return str(round(math.expm1(value)))

    def band(f: dict[str, float]) -> str:
        return next((b for b in ("common", "uncommon", "rarest") if f[b]), "unknown")

    typer.echo(
        f"{case.id}: confirmed {case.disease_label} ({case.disease_id}); "
        f"{len(case.hpo_ids)} findings; {len(rows)} candidates"
    )
    header = ("model", "phenotype", "patients", "explained", "contradicted", "missing")
    typer.echo(
        f"{'disease':<36}"
        + "".join(f"{h:>13}" for h in header)
        + f"{'annotated':>10}{'prevalence':>11}{'v1.1':>6}  right"
    )
    order = sorted(rows, key=lambda r: [-r.features[x] for x in ("model", "phenotype", "patients")])
    for r in order:
        f = r.features
        typer.echo(
            f"{names[r.disease_id][:35]:<36}{place(f['model']):>13}{place(f['phenotype']):>13}"
            f"{place(f['patients']):>13}{f['explained']:>13.0%}{f['contradicted']:>13.0f}"
            f"{count(f['missing']):>13}{count(f['annotations']):>10}{band(f):>11}"
            f"{place(f['v1.1']):>6}  {'yes' if r.correct else ''}"
        )


@eval_app.command("calibrate")
def calibrate(
    config: Annotated[
        Path | None,
        typer.Option(help="The recorded runs per source. Default: evals/calibration.toml."),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option(help="Write each case's verdicts (TSV), for paired comparisons."),
    ] = None,
    show: Annotated[
        str | None,
        typer.Option(help="Only print one case's pool, a row of evidence per candidate."),
    ] = None,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Rank every route's candidates by weights learned on the other development sources,
    beside the recorded agents (chapter 30). No model is called."""
    import tomllib

    import mlflow

    from raredx.baselines.similar_patients import SimilarPatientsRank
    from raredx.evals import hits
    from raredx.evals.harness import candidates_of
    from raredx.evals.systems import Candidate
    from raredx.knowledge import prevalence
    from raredx.ranking import model as scorer
    from raredx.ranking.pool import FEATURES, Pool, Row, accepted
    from raredx.tools.check_match import CheckMatch

    path = config or evals_dir / CALIBRATION
    listed = tomllib.loads(path.read_text(encoding="utf-8"))["source"]
    tests = [
        s["split"]
        for s in listed
        if s["split"].startswith("heldout")
        or (s["split"] in splits.EXTERNAL and s["split"] not in splits.PRACTICE)
    ]
    if tests:
        _fail(f"{path}: {', '.join(tests)} test a frozen system — never calibrate on them")
    harness = _harness()

    def recorded(run_id: str) -> dict[str, list[Candidate]]:
        return {
            t.data.spans[0].inputs["question"]["case_id"]: candidates_of(t.data.spans[0].outputs)
            for t in harness.answers(run_id)
        }

    to_score = []
    for source in listed:
        split = source["split"]
        _, asked = _processed(data_dir, evals_dir, splits.dataset_of(split, DATASET))
        by_id = {c.id: c for c in asked}
        cases = [by_id[case_id] for case_id, _ in splits.read(_manifest(evals_dir, split))]
        if show:
            cases = [c for c in cases if c.id == show]
            if not cases:
                continue
        answers = {name: recorded(source[name]) for name in CALIBRATED}
        for name, got in answers.items():
            if {c.id for c in cases} - set(got):
                _fail(f"{split}: run {source[name]} ({name}) did not answer every case")
        to_score.append((split, cases, answers))

    _, release = _processed(data_dir, evals_dir)
    ranker = _ranker(evals_dir, data_dir, None)
    patients = SimilarPatientsRank(_patient_bank(release, evals_dir, data_dir))
    files = _orphanet_prevalence_files(evals_dir, data_dir)
    bands = prevalence.disease_bands(*files, _identity(evals_dir, data_dir).same)
    pool = Pool(ranker, CheckMatch(ranker.hpo), patients, bands)
    rows: list[Row] = []
    mlflow.tracing.disable()  # tens of thousands of tool calls, none of them an evaluation's
    try:
        for split, cases, answers in to_score:
            for case in cases:
                agent = [
                    d
                    for c in answers["v1.1"][case.id]
                    if (d := scoring.normalize_disease(c.disease_id))
                ]
                rows += pool.rows(split, case, answers["model"][case.id], {"v1.1": agent})
    finally:
        mlflow.tracing.enable()
    if show:
        if not to_score:
            _fail(f"{show} is in none of the sources of {path}")
        _show_pool(to_score[0][1][0], rows, ranker.hpo.names)
        return

    variants = {"scorer": FEATURES, "scorer+v1.1": (*FEATURES, "v1.1")}
    orders = {name: scorer.other_sources(rows, f) for name, f in variants.items()}
    orders |= {f"{name}/same": scorer.same_source(rows, f) for name, f in variants.items()}
    in_pool = {r.case_id for r in rows if r.correct}
    table = []
    for split, cases, answers in to_score:
        for case in cases:
            truth = accepted(case)
            rank = {
                name: scoring.ranks(got[case.id], case.disease_id, None, case.also_accepted)[0]
                for name, got in answers.items()
            }
            for name, order in orders.items():
                ids = order.get(case.id, [])
                rank[name] = next((i for i, d in enumerate(ids, 1) if d in truth), None)
            row = {
                "source": split,
                "case_id": case.id,
                "answerable": str(int(hits.answerable(case, ranker.hpo))),
                "in_pool": str(int(case.id in in_pool)),
            }
            row |= {
                f"{n}@{k}": str(int(scoring.found(r, k)))
                for n, r in rank.items()
                for k in scoring.KS
            }
            table.append(row)

    names = (*CALIBRATED, *orders)
    typer.echo(
        f"First place ({len(rows)} candidates). scorer: weights learned on the other sources; "
        "/same: on other folds of the same source (optimistic)."
    )
    typer.echo(f"{'source':<19}{'cases':>6}{'in pool':>9}" + "".join(f"{n:>17}" for n in names))
    for split, _, _ in to_score:
        mine = [r for r in table if r["source"] == split]

        def share(column: str, of: list[dict[str, str]] = mine) -> str:
            return f"{sum(r[column] == '1' for r in of) / len(of):.1%}"

        typer.echo(
            f"{split:<19}{len(mine):>6}{share('in_pool'):>9}"
            + "".join(f"{share(f'{n}@1'):>17}" for n in names)
        )
    typer.echo("\nPaired, first place (only the first right : only the second right):")
    for split, _, _ in to_score:
        mine = [r for r in table if r["source"] == split]
        pairs = []
        for a, b in (("scorer", "v1.1"), ("scorer+v1.1", "v1.1")):
            w = sum(r[f"{a}@1"] == "1" and r[f"{b}@1"] == "0" for r in mine)
            loss = sum(r[f"{b}@1"] == "1" and r[f"{a}@1"] == "0" for r in mine)
            pairs.append(f"{a} vs {b} {w}:{loss} {scoring.p_value(scoring.sign_test(w, loss))}")
        typer.echo(f"  {split:<19}" + "   ".join(pairs))
    learned = scorer.weights(scorer.fit(rows, FEATURES), FEATURES)
    typer.echo(
        "\nWeights of scorer, learned on every source (per standard deviation), largest first:"
    )
    by_size = sorted(learned.items(), key=lambda fw: -abs(fw[1]))
    typer.echo("  " + "  ".join(f"{f} {w:+.2f}" for f, w in by_size))
    if out:
        hits.write(table, out)
        typer.echo(f"\nok  {out}  ({len(table)} cases)")


@eval_app.command("lenient")
def lenient_judge(
    split: Annotated[str, typer.Option(help="The manifest whose cases are judged.")],
    run: Annotated[
        list[str],
        typer.Option(help="NAME=RUN_ID (or RUN_ID+FILL_ID): a system's run to judge; repeatable."),
    ],
    out: Annotated[Path, typer.Option(help="Where the ranks are kept (JSON); read back first.")],
    budget_usd: Annotated[
        float, typer.Option(help="Stop calling the judge once this much is spent.")
    ] = 0.5,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Judge recorded answers DeepRare's way: deepseek-flash reads each system's five
    names and the confirmed diagnosis, and gives the rank it is named at, or none."""
    from raredx import llm
    from raredx.evals import lenient
    from raredx.evals.harness import candidates_of

    _, pool = _processed(data_dir, evals_dir, splits.dataset_of(split, DATASET))
    by_id = {c.id: c for c in pool}
    cases = [by_id[case_id] for case_id, _ in splits.read(_manifest(evals_dir, split))]
    harness = _harness()
    names: dict[str, dict[str, list[str]]] = {c.id: {} for c in cases}
    for item in run:
        system, _, chain = item.partition("=")
        for run_id in chain.split("+"):  # a fill-in run's answers replace the lost ones
            for trace in harness.answers(run_id):
                case_id = trace.data.spans[0].inputs["question"]["case_id"]
                if case_id in names:
                    found = candidates_of(trace.data.spans[0].outputs)
                    names[case_id][system] = [c.disease_name for c in found]
        missing = [c.id for c in cases if system not in names[c.id]]
        if missing:
            _fail(f"{system}: no recorded answer to {len(missing)} of the cases")
    prices = (settings.llm_price_input, settings.llm_price_cached_input, settings.llm_price_output)
    budget = llm.Budget(budget_usd, prices)
    judge = lenient.Judge(_model_client(), settings.llm_model, budget)
    rows = lenient.judge_all(judge, names, {c.id: c.disease_label for c in cases}, out)
    for item in run:
        system = item.partition("=")[0]
        ranks = [row[system] for row in rows]
        top = {k: sum(isinstance(r, int) and r <= k for r in ranks) for k in (1, 5)}
        typer.echo(
            f"{system:<12} top-1 {top[1] / len(rows):6.1%}   top-5 {top[5] / len(rows):6.1%}"
        )
    typer.echo(f"ok  {out}  ({len(rows)} cases; about ${budget.spent:.4f} at peak price)")


# The development sources (docs/roadmap.md, section 5.1): never a test set.
DEVELOPMENT = ("dev-200", "rarebench-hms", "rarebench-ramedis", "rarebench-mme", splits.RAREARENA)


def _development_cases(evals_dir: Path, data_dir: Path) -> dict[str, list[Case]]:
    out = {}
    for name in DEVELOPMENT:
        _, pool = _processed(data_dir, evals_dir, splits.dataset_of(name, DATASET))
        by_id = {c.id: c for c in pool}
        out[name] = [by_id[case_id] for case_id, _ in splits.read(_manifest(evals_dir, name))]
    return out


@eval_app.command("rankers")
def rankers(
    data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir
) -> None:
    """The no-model rank-then-check, for every similarity (F funSimAvg, O one-way, FO their
    fusion), order of the top 30 (N as ranked, C findings explained, I their information
    content) and knowledge (OMIM, merged with Orphanet), on every development source;
    each against the default by the rule fixed beforehand. No model is called."""
    import mlflow

    from raredx.evals import offline

    cases = _development_cases(evals_dir, data_dir)
    knowledge = {
        "OMIM": _knowledge(evals_dir, data_dir, orphanet=False),
        "merged": _knowledge(evals_dir, data_dir, orphanet=True),
    }
    mlflow.tracing.disable()  # tens of thousands of tool calls, none of them an evaluation's
    try:
        rows = offline.rankers(knowledge, cases, _identity(evals_dir, data_dir).same)
    finally:
        mlflow.tracing.enable()
    configs = sorted({(r["knowledge"], r["ranker"], r["order"]) for r in rows})
    short = [s.replace("rarebench-", "") for s in cases]
    typer.echo("First place / top ten, rank-then-check without a model:")
    typer.echo(f"{'':<16}" + "".join(f"{s:>16}" for s in short))
    for config in configs:
        cells = []
        for source in cases:
            ranks = [
                r["rank"]
                for r in rows
                if (r["knowledge"], r["ranker"], r["order"]) == config and r["source"] == source
            ]
            top1 = sum(x == 1 for x in ranks) / len(ranks)
            top10 = sum(x is not None for x in ranks) / len(ranks)
            cells.append(f"{top1:.1%}/{top10:.1%}")
        mark = "  (default)" if config == offline.BASELINE else ""
        typer.echo(f"{' '.join(config):<16}" + "".join(f"{c:>16}" for c in cells) + mark)
    typer.echo(
        "\nAgainst the default (only this right : only the default right, first place / top "
        "ten; * p < 0.05). PASS: no source significantly worse, two significantly better."
    )
    for config in configs:
        if config == offline.BASELINE:
            continue
        v = offline.verdict(rows, config)
        cells = [
            "/".join(
                f"{w}:{lost}{'*' if p < 0.05 else ''}" for w, lost, p in v["sources"][s].values()
            )
            for s in cases
        ]
        typer.echo(
            f"{' '.join(config):<16}"
            + "".join(f"{c:>16}" for c in cells)
            + ("   PASS" if v["pass"] else "")
        )


# Chapter 33: the RAG corpus (five text sources as structured documents), its indexes
# (one per way of chunking and embedding model) and their evaluation. No model.

RAG_TEXTS = (
    "genereviews",
    "genereviews-omim",
    "wikipedia",
    "orphanet",
    "mondo-ontology",
    "medlineplus",
)
RAG_SOURCES = (
    "dev-200",
    "rarebench-hms",
    "rarebench-ramedis-200",
    "rarebench-mme",
    "rarearena-dev",
)
RAG_EXPERIMENT = "rag-retrieval"
DOCUMENTS = "documents.jsonl"
CHAPTER18 = "chapter18"  # eval rag's name for chapter 18's index
RAG_SEED = 20261023  # which other GeneReviews chapters a sample draws


def _rag_corpus_dir(evals_dir: Path, data_dir: Path) -> Path:
    registry = sources.load_sources(evals_dir / "datasets.toml")
    names = ("genereviews", "wikipedia", "orphanet", "mondo-ontology", "medlineplus")
    versions = "_".join(f"{n}-{registry[n].version}" for n in names)
    return data_dir / "processed" / "rag-corpus" / versions


def _rag_documents(evals_dir: Path, data_dir: Path) -> list["Document"]:
    from raredx.knowledge.corpus import Document

    path = _rag_corpus_dir(evals_dir, data_dir) / DOCUMENTS
    if not path.exists():
        _fail(f"{path} missing — run `raredx data corpus` first")
    with path.open(encoding="utf-8") as f:
        return [Document.model_validate_json(line) for line in f]


@data_app.command("corpus")
def build_corpus(
    data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir
) -> None:
    """Read the five text sources — GeneReviews, Wikipedia, Orphanet, Mondo, MedlinePlus
    — into structured documents about the knowledge's diseases (Orphanet merged in).
    Every file is verified first. No model."""
    from raredx.data import wikipedia
    from raredx.knowledge import corpus

    registry = sources.load_sources(evals_dir / "datasets.toml")
    for name in RAG_TEXTS:
        sources.fetch(registry[name], data_dir)  # downloads what is missing; verifies all
    raw = {name: sources.raw_dir(registry[name], data_dir) for name in RAG_TEXTS}
    knowledge = _knowledge(evals_dir, data_dir, orphanet=True)
    readers = {
        "genereviews": corpus.genereviews(
            raw["genereviews"] / corpus.GENEREVIEWS_BOOK,
            raw["genereviews-omim"] / corpus.GENEREVIEWS_OMIM,
        ),
        "wikipedia": corpus.wikipedia(
            wikipedia.pages(raw["wikipedia"] / wikipedia.PAGES),
            {
                a.revid: [*a.orpha, *a.omim]
                for a in wikipedia.read_manifest(evals_dir / WIKIPEDIA_REVISIONS)
            },
        ),
        "orphanet": corpus.orphanet(raw["orphanet"] / corpus.ORPHANET),
        "mondo": corpus.mondo(
            raw["mondo-ontology"] / corpus.MONDO, _identity(evals_dir, data_dir).classes()
        ),
        "medlineplus": corpus.medlineplus(raw["medlineplus"] / corpus.MEDLINEPLUS),
    }
    folder = _rag_corpus_dir(evals_dir, data_dir)
    folder.mkdir(parents=True, exist_ok=True)
    covered: set[str] = set()
    counts = {}
    with (folder / DOCUMENTS).open("w", encoding="utf-8") as f:
        for name, read in readers.items():
            docs = list(corpus.resolve(read, knowledge))
            for doc in docs:
                f.write(doc.model_dump_json() + "\n")
            diseases = {d for doc in docs for d in doc.disease_ids}
            covered |= diseases
            counts[name] = {
                "documents": len(docs),
                "diseases": len(diseases),
                "words": sum(doc.words() for doc in docs),
            }
            typer.echo(
                f"   {name:<12} {len(docs):>6} documents  {len(diseases):>6} diseases  "
                f"{counts[name]['words'] / 1e6:.1f}M words"
            )
    share = len(covered) / len(knowledge.names)
    build = {
        "sources": {n: registry[n].version for n in RAG_TEXTS},
        "hpo_release": knowledge.release,
        "knowledge": _knowledge_label(evals_dir),
        "counts": counts,
        "diseases_with_text": len(covered),
        "diseases": len(knowledge.names),
    }
    (folder / "build.json").write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    typer.echo(
        f"ok  {folder}  ({len(covered)} of {len(knowledge.names)} diseases have a text, "
        f"{share:.0%})"
    )


def _rag_questions(evals_dir: Path, data_dir: Path) -> list["RagQuestion"]:
    """The questions of chapter 33, each fact question once (a source without papers
    asks the same one of each case with the disease)."""
    from raredx.evals import rag

    registry = sources.load_sources(evals_dir / "datasets.toml")
    key = rag.inheritance_key(
        sources.raw_dir(registry["orphanet-ages"], data_dir) / "en_product9_ages.xml"
    )
    cases = {}
    for name in RAG_SOURCES:
        _, pool = _processed(data_dir, evals_dir, splits.dataset_of(name, DATASET))
        by_id = {c.id: c for c in pool}
        cases[name] = [by_id[case_id] for case_id, _ in splits.read(_manifest(evals_dir, name))]
    asked = rag.questions(
        cases,
        _knowledge(evals_dir, data_dir, orphanet=True),
        _identity(evals_dir, data_dir).same,
        key,
    )
    seen, out = set(), []
    for q in asked:
        key_ = (q.kind, q.text, tuple(q.hide_pmids), q.source) if q.kind != "find" else q.case_id
        if key_ not in seen:
            seen.add(key_)
            out.append(q)
    return out


def _rag_index_dir(data_dir: Path, name: str) -> Path:
    return data_dir / "processed" / "rag-index" / name


@data_app.command("rag-index")
def rag_index(
    name: Annotated[str, typer.Argument(help="The index's name, e.g. gr-section+context.")],
    strategy: Annotated[
        str, typer.Option(help="fixed | recursive | section | section+context | parent")
    ] = "section+context",
    model: Annotated[
        str, typer.Option(help="The dense model (FastEmbed's name).")
    ] = "BAAI/bge-small-en-v1.5",
    source: Annotated[
        list[str] | None, typer.Option(help="Only these corpus sources; repeatable.")
    ] = None,
    chapters: Annotated[
        int,
        typer.Option(
            help="GeneReviews only: this many chapters — every one about a question's "
            "disease, then others drawn at random."
        ),
    ] = 0,
    threads: Annotated[int, typer.Option(help="CPU cores to embed with (leave some free).")] = 6,
    force: Annotated[bool, typer.Option(help="Embed again though the index exists.")] = False,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Chunk the corpus one way and embed it with one model, into an index (kept: an
    index already built is left as it is, unless --force). Embedding
    is slow on a laptop (about 20 chunks a second); a progress line every 2,000."""
    import random

    import numpy as np

    from raredx.knowledge import chunking
    from raredx.knowledge.text_index import FastEmbedder, TextIndex

    if strategy not in chunking.STRATEGIES:
        _fail(f"{strategy}: choose one of {', '.join(chunking.STRATEGIES)}")
    built = _rag_index_dir(data_dir, name) / "index.json"
    if built.exists() and not force:
        info = json.loads(built.read_text(encoding="utf-8"))
        typer.echo(
            f"ok  {built.parent}  (built before: {info['passages']} chunks, "
            f"{info['strategy']}, {info['dense']}; --force to embed again)"
        )
        return
    docs = [d for d in _rag_documents(evals_dir, data_dir) if not source or d.source in source]
    if chapters:
        asked = {q.disease for q in _rag_questions(evals_dir, data_dir)}
        chosen = [d for d in docs if d.source == "genereviews"]
        about = [d for d in chosen if asked & set(d.disease_ids)]
        others = [d for d in chosen if d not in about]
        random.Random(RAG_SEED).shuffle(others)
        docs = sorted(about + others[: max(0, chapters - len(about))], key=lambda d: d.id)
    chunks = [c for d in docs for c in chunking.chunk(d, strategy)]
    typer.echo(
        f"embedding {len(chunks)} chunks of {len(docs)} documents with {model} ...", err=True
    )
    embedder = FastEmbedder(data_dir / "models", model, threads)
    dense_parts, sparse = [], []
    for start in range(0, len(chunks), 2000):
        d, s = embedder.passages([c.text for c in chunks[start : start + 2000]])
        dense_parts.append(d)
        sparse += s
        typer.echo(f"   {min(start + 2000, len(chunks))} of {len(chunks)}", err=True)
    info = {
        "corpus": _rag_corpus_dir(evals_dir, data_dir).name,
        "strategy": strategy,
        "documents": len(docs),
        "sources": sorted({d.source for d in docs}),
    }
    folder = _rag_index_dir(data_dir, name)
    TextIndex.save(folder, chunks, np.vstack(dense_parts), sparse, info, dense_model=model)
    typer.echo(f"ok  {folder}  ({len(chunks)} chunks)")


@eval_app.command("rag")
def eval_rag(
    index: Annotated[
        list[str], typer.Option(help="An index built by `data rag-index`; repeatable.")
    ],
    mode: Annotated[str, typer.Option(help="hybrid | dense | keyword")] = "hybrid",
    filtered: Annotated[
        bool, typer.Option(help="Fact questions search only the disease's chunks.")
    ] = False,
    rerank: Annotated[
        str,
        typer.Option(
            help="A cross-encoder to rerank fact questions' 30 best, "
            "e.g. Xenova/ms-marco-MiniLM-L-6-v2."
        ),
    ] = "",
    covered: Annotated[
        bool, typer.Option(help="Only questions on a disease the index has text on.")
    ] = False,
    kind: Annotated[
        list[str] | None, typer.Option(help="find | inheritance | feature; repeatable.")
    ] = None,
    threads: Annotated[int, typer.Option(help="CPU cores for the query and rerank models.")] = 6,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Retrieval measured on chapter 33's questions, under each case's mask: per index,
    the questions whose disease it has any text on (its coverage, reported first), and
    each measure per kind and source. Each index's result is an MLflow run in the
    rag-retrieval experiment. No model is called."""
    import mlflow
    from mlflow import MlflowClient

    from raredx.evals import rag
    from raredx.knowledge.text_index import INFO, TextIndex
    from raredx.knowledge.texts import Passage

    config = rag.Config(mode=mode, filtered=filtered, rerank=rerank)  # type: ignore[arg-type]
    asked = [q for q in _rag_questions(evals_dir, data_dir) if not kind or q.kind in kind]
    reranker = None
    if rerank:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        encoder = TextCrossEncoder(rerank, cache_dir=str(data_dir / "models"), threads=threads)

        def reranker(query: str, texts: list[str]) -> list[float]:
            return list(encoder.rerank(query, texts))

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    client = MlflowClient()
    if client.get_experiment_by_name(RAG_EXPERIMENT) is None:
        location = (settings.mlflow_artifact_root / RAG_EXPERIMENT).resolve().as_uri()
        client.create_experiment(RAG_EXPERIMENT, artifact_location=location)
    mlflow.set_experiment(RAG_EXPERIMENT)
    for name in index:
        if name == CHAPTER18:  # the index chapter 18 built, read as it was
            registry = sources.load_sources(evals_dir / "datasets.toml")
            release = _knowledge(evals_dir, data_dir).release
            folder = _text_index_dir(registry, data_dir, release)
        else:
            folder = _rag_index_dir(data_dir, name)
        if not (folder / INFO).exists():
            _fail(f"{folder} has no index — run `raredx data rag-index {name}` first")
        text_index = TextIndex.open(
            folder, data_dir / "models", Passage, threads, location=settings.qdrant_url
        )
        text_index.info.setdefault("strategy", "chapter 18: one definition or paragraph each")
        has_text = {d for p in text_index.passages for d in p.disease_ids}
        mine = [q for q in asked if q.disease in has_text or not covered]
        rows = []
        for q in mine:
            rows.append(
                {
                    "kind": q.kind,
                    "source": q.source,
                    "question": q.text,
                    "scores": rag.score(q, rag.ask(text_index, q, config, reranker)),
                }
            )
        results = rag.summary(rows)
        typer.echo(
            f"{name} ({text_index.info['strategy']}, {text_index.info['dense']}; "
            f"{len(text_index.passages)} chunks) — {config.label()}; "
            f"{len(mine)} of {len(asked)} questions asked; "
            f"{sum(q.disease in has_text for q in asked)} on a disease it has text on"
        )
        for group in sorted(results):
            measures = "  ".join(f"{m} {v:.1%}" for m, v in results[group].items() if m != "n")
            typer.echo(f"   {group:<32} n {results[group]['n']:>5}  {measures}")
        with mlflow.start_run(run_name=f"{name} | {config.label()}"):
            mlflow.log_params(
                {
                    **{k: str(v) for k, v in text_index.info.items()},
                    "index": name,
                    "mode": mode,
                    "filtered": filtered,
                    "rerank": rerank or "none",
                    "questions": len(mine),
                    "asked": len(asked),
                }
            )
            mlflow.log_metrics(
                {
                    f"{group}.{m}".replace("@", "_at_").replace("/", ".").replace("+", "_"): v
                    for group, measures in results.items()
                    for m, v in measures.items()
                }
            )
            mlflow.log_table(
                {
                    k: [r[k] if k != "scores" else json.dumps(r[k]) for r in rows]
                    for k in ("kind", "source", "question", "scores")
                },
                artifact_file="questions.json",
            )


@eval_app.command("rag-runs")
def rag_runs(
    prefix: Annotated[
        list[str] | None, typer.Option(help="Only runs whose name starts so.")
    ] = None,
    measure: Annotated[
        list[str] | None, typer.Option(help="kind.measure columns, e.g. feature.answer@5.")
    ] = None,
) -> None:
    """The recorded `eval rag` runs, the latest of each name, as one table: what each
    configuration scored, read from MLflow rather than run again."""
    import mlflow

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    runs = mlflow.search_runs(experiment_names=[RAG_EXPERIMENT], order_by=["start_time DESC"])
    columns = measure or [
        "find.disease@10",
        "feature.answer@5",
        "inheritance.answer@5",
        "inheritance.rr",
    ]
    typer.echo(f"{'run':<64}{'n':>6}" + "".join(f"{c:>22}" for c in columns))
    seen: set[str] = set()
    for _, run in runs.iterrows():
        name = str(run["tags.mlflow.runName"])
        if name in seen or (prefix and not name.startswith(tuple(prefix))):
            continue
        seen.add(name)
        cells = []
        for c in columns:
            value = run.get("metrics." + c.replace("@", "_at_"))
            cells.append("-" if value is None or value != value else f"{value:.1%}")
        typer.echo(f"{name:<64}{run['params.questions']:>6}" + "".join(f"{c:>22}" for c in cells))


RAG_ANSWERS_EXPERIMENT = "rag-answers"


@eval_app.command("rag-answers")
def rag_answers_command(
    index: Annotated[str, typer.Option(help="The index the open book reads.")],
    n: Annotated[int, typer.Option(help="Inheritance questions to ask (seeded draw).")] = 100,
    budget_usd: Annotated[float, typer.Option(help="Stop once this is spent.")] = 0.20,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """The model asked how diseases are inherited, closed book and open book (the
    index's five passages on the disease, masked), scored against Orphanet by code. Two
    model calls a question; every call traced in the rag-answers experiment."""
    import mlflow
    from mlflow import MlflowClient

    from raredx import llm
    from raredx.evals import rag_answers
    from raredx.knowledge.text_index import TextIndex
    from raredx.knowledge.texts import Passage

    folder = _rag_index_dir(data_dir, index)
    text_index = TextIndex.open(
        folder, data_dir / "models", Passage, 2, location=settings.qdrant_url
    )
    has_text = {d for p in text_index.passages for d in p.disease_ids}
    asked = rag_answers.sample(
        [q for q in _rag_questions(evals_dir, data_dir) if q.disease in has_text], n
    )
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    client = MlflowClient()
    if client.get_experiment_by_name(RAG_ANSWERS_EXPERIMENT) is None:
        location = (settings.mlflow_artifact_root / RAG_ANSWERS_EXPERIMENT).resolve().as_uri()
        client.create_experiment(RAG_ANSWERS_EXPERIMENT, artifact_location=location)
    mlflow.set_experiment(RAG_ANSWERS_EXPERIMENT)
    api = llm.client(settings)
    budget, tally = llm.Budget(budget_usd, _prices()), llm.Tally()
    with mlflow.start_run(run_name=f"{index} | {len(asked)} questions"):
        results = rag_answers.run(text_index, asked, api, settings.llm_model, budget, tally)
        s = rag_answers.summary(results)
        mlflow.log_params(
            {
                "index": index,
                "model": settings.llm_model,
                "questions": len(asked),
                "prompt_version": rag_answers.PROMPT_VERSION,
            }
        )
        mlflow.log_metrics(
            {f"{book}.{m}": v for book in ("closed", "open") for m, v in s[book].items()}
            | {"passages_say_it": s["passages_say_it"], "cost_usd": tally.cost(settings)}
        )
        mlflow.log_table(
            {k: [str(getattr(r, k)) for r in results] for k in rag_answers.Result.model_fields},
            artifact_file="answers.json",
        )
    typer.echo(
        f"{len(asked)} questions on {index}; {tally.model_calls} model calls, "
        f"${tally.cost(settings):.4f} at the peak price"
    )
    for book in ("closed", "open"):
        line = "  ".join(f"{m} {v:.1%}" for m, v in s[book].items())
        typer.echo(f"   {book + ' book':<11} {line}")
    typer.echo(
        f"   passages say the truth {s['passages_say_it']:.1%}; open book right when they "
        f"do {s['open_right_when_passages_say_it']:.1%}"
    )


@eval_app.command("rag-compare")
def rag_compare(
    run: Annotated[
        list[str], typer.Option(help="Two run names of `eval rag`, e.g. 'gr300-fixed | hybrid'.")
    ],
    measure: Annotated[
        list[str] | None, typer.Option(help="kind:measure, e.g. feature:answer@5; repeatable.")
    ] = None,
) -> None:
    """Two `eval rag` runs, question by question (the latest run of each name): for each
    measure, how many questions only the first gets, only the second, and the sign
    test's p. No model is called."""
    import mlflow

    from raredx.evals import rag

    if len(run) != 2:
        _fail("give two --run names")
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    rows = []
    for name in run:
        found = mlflow.search_runs(
            experiment_names=[RAG_EXPERIMENT],
            filter_string=f"tags.mlflow.runName = '{name}'",
            order_by=["start_time DESC"],
            max_results=1,
        )
        if found.empty:
            _fail(f"no run named {name!r} in {RAG_EXPERIMENT}")
        first = found.iloc[0]
        table = mlflow.MlflowClient().load_table(
            first.experiment_id, "questions.json", run_ids=[first.run_id]
        )
        rows.append([{**r, "scores": json.loads(r["scores"])} for r in table.to_dict("records")])
    wanted = measure or [
        "find:disease@10",
        "feature:answer@5",
        "inheritance:answer@5",
        "inheritance:rr",
    ]
    typer.echo(f"only {run[0]!r} : only {run[1]!r}")
    for item in wanted:
        kind, _, m = item.partition(":")
        a, b, p = rag.paired(rows[0], rows[1], kind, m)  # type: ignore[arg-type]
        typer.echo(f"   {item:<24} {a:>4} : {b:<4} p = {p:.3f}{'  *' if p < 0.05 else ''}")


@eval_app.command("routes")
def routes(data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir) -> None:
    """How often the confirmed disease is among the candidates the agent would see, for
    each mix of nominating routes: M the model's own answer (read from the recorded runs
    in evals/calibration.toml), F funSimAvg, O one-way, C similar case reports, P similar
    Phenopacket patients; ten each. No model is called."""
    import tomllib

    import mlflow

    from raredx.baselines.similar_patients import SimilarPatientsRank
    from raredx.evals import offline
    from raredx.evals.harness import candidates_of

    cases = _development_cases(evals_dir, data_dir)
    kb = _knowledge(evals_dir, data_dir)
    listed = tomllib.loads((evals_dir / CALIBRATION).read_text(encoding="utf-8"))["source"]
    harness = _harness()
    model: dict[str, list[str]] = {}
    for source in listed:
        for trace in harness.answers(source["model"]):
            case_id = trace.data.spans[0].inputs["question"]["case_id"]
            ids = [
                scoring.normalize_disease(c.disease_id)
                for c in candidates_of(trace.data.spans[0].outputs)
            ]
            model[case_id] = [kb.canonical(d) or d for d in ids if d]
    _, release = _processed(data_dir, evals_dir)
    patients = SimilarPatientsRank(_patient_bank(release, evals_dir, data_dir))
    mlflow.tracing.disable()
    try:
        rows = offline.routes(
            kb,
            cases,
            _identity(evals_dir, data_dir).same,
            model,
            _case_bank(evals_dir, data_dir),
            patients,
        )
    finally:
        mlflow.tracing.enable()
    mixes = (
        "F",
        "O",
        "C",
        "P",
        "M",
        "F+O",
        "F+C",
        "F+O+C+P",  # the routes no model is asked for, recorded on every source
        "M+F",
        "M+F+O",
        "M+F+C",
        "M+F+P",
        "M+F+O+C",
        "M+F+O+C+P",
    )
    short = [s.replace("rarebench-", "") for s in cases]
    typer.echo(f"Confirmed disease among the candidates ({kb!r}; - = route not recorded):")
    typer.echo(f"{'routes':<12}" + "".join(f"{s:>15}" for s in short))
    for mix in mixes:
        cells = []
        for source in cases:
            value = offline.coverage([r for r in rows if r["source"] == source], mix)
            cells.append("-" if value is None else f"{value:.1%}")
        typer.echo(f"{mix:<12}" + "".join(f"{c:>15}" for c in cells))


@eval_app.command("coverage")
def coverage(
    split: Annotated[list[str], typer.Option(help="A manifest whose cases to count; repeatable.")],
    show: Annotated[
        int, typer.Option(help="List up to this many cases that one version alone can answer.")
    ] = 10,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """How many cases a system could answer at all, with Orphanet's annotations and without:
    the confirmed diagnosis, or a disease Mondo makes equal to it (as when scored), names a
    disease in the knowledge that the case's mask does not hide. A case answerable only
    with Orphanet is listed: its own paper may be behind Orphanet's entry too (chapter
    31's leak check). No model is called."""
    from raredx.evals import hits

    tests = [s for s in split if s.startswith("heldout") or s == splits.TEMPORAL]
    if tests:
        _fail(f"{', '.join(tests)}: a test set is not looked into while developing")
    with_orphanet = _knowledge(evals_dir, data_dir, orphanet=True)
    omim_only = _knowledge(evals_dir, data_dir, orphanet=False)  # the same release
    same = _identity(evals_dir, data_dir).same  # a diagnosis's equals count, as when scored
    typer.echo(f"{'cases answerable':<24}{'cases':>7}{'OMIM only':>11}{'+ Orphanet':>12}")
    for name in split:
        _, pool = _processed(data_dir, evals_dir, splits.dataset_of(name, DATASET))
        by_id = {c.id: c for c in pool}
        cases = [by_id[case_id] for case_id, _ in splits.read(_manifest(evals_dir, name))]
        before = {c.id for c in cases if hits.answerable(c, omim_only, same)}
        after = {c.id for c in cases if hits.answerable(c, with_orphanet, same)}
        typer.echo(f"{name:<24}{len(cases):>7}{len(before):>11}{len(after):>12}")
        for sign, ids in (("+", after - before), ("-", before - after)):
            listed = [c for c in cases if c.id in ids]
            for case in listed[:show]:
                here = with_orphanet.canonical(case.disease_id) or "-"
                typer.echo(
                    f"   {sign} {case.id:<34}{case.disease_id:<13}{here:<13}"
                    f"{case.disease_label[:44]}"
                )
            if len(listed) > show:
                typer.echo(f"   {sign} … and {len(listed) - show} more")


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
    width = max(len(header[1]), *(len(r["name"]) for r in rows))
    line = "{:<17} {:<{w}} {:>9} {:>10} {:>8}  {:<14} {}"
    typer.echo(line.format(*header, w=width))
    for r in rows:
        started = datetime.fromtimestamp(r["start_time"] / 1000).strftime("%Y-%m-%d %H:%M")
        scores = [pct(r["disease_top1"]), pct(r["disease_top10"]), pct(r["gene_top10"])]
        cells = [started, r["name"], *scores, r["code"], r["run_id"]]
        typer.echo(line.format(*cells, w=width))


# ── mcp ─────────────────────────────────────────────────────────────


@app.command("mcp")
def serve_mcp(
    transport: Annotated[
        str,
        typer.Option(
            help="stdio: for a host that launches this command. "
            "streamable-http: to serve the tools at a URL."
        ),
    ] = "stdio",
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Serve the tools over MCP, for Claude Code, Claude Desktop or an agent to call."""
    if transport not in ("stdio", "streamable-http"):
        _fail(f"unknown transport {transport!r}: choose stdio or streamable-http")
    import logging

    import mlflow

    from raredx.mcp_server import build

    knowledge = _knowledge(evals_dir, data_dir)
    # Serving is not an exam: the patient bank holds every published patient.
    out_dir = sources.processed_dir(_source(evals_dir), data_dir)
    extra: list[object] = []
    if (out_dir / case_store.CASES_FILE).exists():
        extra.append(
            _patient_bank(
                case_store.read(out_dir), evals_dir, data_dir, splits_used=("design", "heldout")
            )
        )
    else:
        typer.echo("no processed cases: serving without find_similar_patients", err=True)
    from raredx.tools.rank_candidate_genes import RankCandidateGenes

    extra.append(RankCandidateGenes(knowledge))
    registry = sources.load_sources(evals_dir / "datasets.toml")
    if (_text_index_dir(registry, data_dir, knowledge.release) / "index.json").exists():
        extra.append(_text_search(evals_dir, data_dir))
    else:
        typer.echo("no text index: serving without search_disease_texts", err=True)
    # A host shows the server's stderr as its log; keep MLflow's routine INFO lines out.
    logging.getLogger("mlflow").setLevel(logging.WARNING)
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("mcp-server")  # every call a host makes is traced here
    server = build(knowledge, extra)
    server.run(transport="streamable-http" if transport == "streamable-http" else "stdio")


# ── notes ───────────────────────────────────────────────────────────


READERS = ("note-reader", "model-direct", "dictionary")
TEST_CORPORA = ("id-68", "gsc-2024-test")


def _term_index_dir(data_dir: Path, hpo_release: str) -> Path:
    return data_dir / "processed" / "hpo-terms" / f"hpo-{hpo_release}"


def _reader(
    name: str, evals_dir: Path, data_dir: Path, budget_usd: float | None = None
) -> "Reader":
    """One of the readers that turn a note into HPO terms; a clear message if it
    cannot be built."""
    from raredx import llm
    from raredx.phenotyping.reader import DictionaryReader, DirectReader

    if name not in READERS:
        _fail(f"unknown reader {name!r}; choose one of: {', '.join(READERS)}")
    knowledge = _knowledge(evals_dir, data_dir)
    if name == "dictionary":
        return DictionaryReader(knowledge)
    prices = (settings.llm_price_input, settings.llm_price_cached_input, settings.llm_price_output)
    budget = llm.Budget(budget_usd, prices) if budget_usd is not None else None
    if name == "model-direct":
        return DirectReader(_model_client(), settings.llm_model, knowledge, budget=budget)
    return _note_reader(evals_dir, data_dir, budget)


def _note_reader(evals_dir: Path, data_dir: Path, budget: "Budget | None" = None) -> "NoteReader":
    """Ours: the model reads, the ontology codes."""
    from raredx.knowledge.text_index import INFO, FastEmbedder, TextIndex
    from raredx.phenotyping.reader import Label, NoteReader

    knowledge = _knowledge(evals_dir, data_dir)
    folder = _term_index_dir(data_dir, knowledge.release)
    if not (folder / INFO).exists():
        _fail(f"{folder} has no term index — run `raredx data hpo-index` first")
    index = TextIndex.load(folder, FastEmbedder(data_dir / "models"), Label)
    return NoteReader(_model_client(), settings.llm_model, knowledge, index, budget=budget)


@app.command("read-note")
def read_note(
    path: Annotated[
        Path | None, typer.Argument(help="A text file. Default: standard input.")
    ] = None,
    reader: Annotated[str, typer.Option(help=" | ".join(READERS))] = "note-reader",
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Read a clinical note into HPO terms. The note goes to the model provider: never
    a real patient's without an agreement with the provider that covers it."""
    import sys

    from raredx import llm

    text = path.read_text(encoding="utf-8") if path else sys.stdin.read()
    chosen = _reader(reader, evals_dir, data_dir)
    tally = llm.Tally()
    findings = chosen.read(text, tally)
    for f in findings:
        code = f"{f.hpo_id}  {f.label}" if f.hpo_id else f"(not coded: {f.uncoded})"
        typer.echo(f'{f.status:<8} {code:<60} "{f.quote}"')
    if tally.model_calls:
        typer.echo(
            f"\n{tally.model_calls} model calls, {tally.input_tokens} tokens in "
            f"({tally.cached_input_tokens} cached), {tally.output_tokens} out, "
            f"about ${tally.cost(settings):.4f}"
        )


@eval_app.command("notes")
def eval_notes(
    corpus: Annotated[
        str, typer.Option(help="id-68 | gsc-2024-test (test); genereviews | gsc-2024-dev")
    ],
    reader: Annotated[str, typer.Option(help=" | ".join(READERS))] = "note-reader",
    final: Annotated[bool, typer.Option(help="Required for a test corpus.")] = False,
    limit: Annotated[int | None, typer.Option(help="Only the first N documents.")] = None,
    budget_usd: Annotated[
        float | None, typer.Option(help="Stop calling the model once this much is spent.")
    ] = None,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Score a reader against text annotated with HPO terms by hand."""
    from raredx.phenotyping import corpora, evaluation

    if corpus not in corpora.CORPORA:
        _fail(f"unknown corpus {corpus!r}; choose one of: {', '.join(corpora.CORPORA)}")
    if corpus in TEST_CORPORA and not final:
        _fail(f"{corpus} is a test set: pass --final, once the reader is settled on the others")
    registry = sources.load_sources(evals_dir / "datasets.toml")
    archive, tarball = (
        sources.raw_dir(registry[name], data_dir) / next(iter(registry[name].files))
        for name in ("phenobert", "gsc-2024")
    )
    if not archive.exists() or not tarball.exists():
        _fail("the corpora are not downloaded — run `raredx data fetch phenobert gsc-2024`")
    documents = corpora.load(corpus, archive, tarball)[:limit]
    chosen = _reader(reader, evals_dir, data_dir, budget_usd)
    run_id, metrics = evaluation.evaluate(
        chosen,
        documents,
        corpus if limit is None else f"{corpus}-first{limit}",
        _knowledge(evals_dir, data_dir),
        tracking_uri=settings.mlflow_tracking_uri,
        artifact_root=settings.mlflow_artifact_root,
        answers=data_dir / "processed" / "notes" / "answers",
        params={"code_version": code_version(), "budget_usd": budget_usd},
    )
    harness = _harness()
    usage = harness.usage(run_id)
    tokens_in, cached = usage["usage/input_tokens"], usage["usage/cached_input_tokens"]
    cost = (
        (tokens_in - cached) * settings.llm_price_input
        + cached * settings.llm_price_cached_input
        + usage["usage/output_tokens"] * settings.llm_price_output
    ) / 1e6
    usage["usage/cost_usd_estimate"] = round(cost, 4)
    harness.log_metrics(run_id, usage)
    n, answered = int(metrics["n_documents"]), int(metrics["n_answered"])
    typer.echo(f"{chosen.name} · {corpus} · {answered} of {n} documents read")
    for scope in ("micro", "macro", "present"):
        p, r, f1 = (metrics[f"{scope}/{m}"] for m in ("precision", "recall", "f1"))
        typer.echo(f"  {scope:<8} precision {p:6.1%}  recall {r:6.1%}  F1 {f1:6.1%}")
    if metrics["negated/n"]:
        typer.echo(
            f"  denied in the note: {int(metrics['negated/n'])} terms; read as absent "
            f"{int(metrics['negated/as_absent'])}, as present {int(metrics['negated/as_present'])}"
        )
    typer.echo(
        f"  {int(metrics['gold/set_aside'])} annotated terms set aside (not findings in this "
        f"release); {int(metrics['usage/read_back'])} readings read back from earlier runs; "
        f"about ${cost:.4f}"
    )
    typer.echo(f"recorded in MLflow: run {run_id}")
    if answered < n:
        _fail(f"{n - answered} documents were not read (model API): run the same command again")


# ── service ─────────────────────────────────────────────────────────


SERVICE_EXPERIMENT = "service"


def _service(data_dir: Path, evals_dir: Path) -> "FastAPI":
    """The HTTP service around the final system, built as the evaluation built it:
    the seeded agent with the patient bank, and the same with the gene tool for
    requests that carry candidate genes. Without a model API key, the fallback alone."""
    import mlflow

    from raredx import llm
    from raredx.agent import Agent
    from raredx.service import examples
    from raredx.service.app import create_app
    from raredx.service.diagnoser import Diagnoser
    from raredx.tools.rank_candidate_genes import RankCandidateGenes

    knowledge = _knowledge(evals_dir, data_dir)
    _, cases = _processed(data_dir, evals_dir)
    used = ("design",) if settings.service_patient_bank == "evaluated" else ("design", "heldout")
    bank = _patient_bank(cases, evals_dir, data_dir, splits_used=used)
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    if mlflow.get_experiment_by_name(SERVICE_EXPERIMENT) is None:
        # A local store keeps the traces' files under the configured root, as the
        # evaluation's experiments do; a tracking server decides for itself.
        local = not settings.mlflow_tracking_uri.startswith("http")
        root = (settings.mlflow_artifact_root / SERVICE_EXPERIMENT).resolve().as_uri()
        mlflow.create_experiment(SERVICE_EXPERIMENT, artifact_location=root if local else None)
    mlflow.set_experiment(SERVICE_EXPERIMENT)  # every request is traced here
    agent = with_genes = unavailable = None
    try:
        model = llm.chat_model(settings, timeout=settings.service_deadline_seconds, max_retries=1)
    except llm.MissingAPIKey:
        unavailable = "no model API key is configured"
        typer.echo("no model API key: serving the no-model ranking only", err=True)
    else:
        name = settings.llm_model
        agent = Agent(model, name, knowledge, seeded=True, extra_tools=[bank])
        with_genes = Agent(
            model, name, knowledge, seeded=True, extra_tools=[bank, RankCandidateGenes(knowledge)]
        )
    diagnoser = Diagnoser(
        knowledge,
        agent=agent,
        agent_with_genes=with_genes,
        unavailable_because=unavailable,
        deadline_seconds=settings.service_deadline_seconds,
        prices=(
            settings.llm_price_input,
            settings.llm_price_cached_input,
            settings.llm_price_output,
        ),
        code=settings.build_version or code_version(),
    )
    reader = None
    if settings.service_read_notes and agent is not None:
        reader = _note_reader(evals_dir, data_dir)
    elif settings.service_read_notes:
        typer.echo("no model API key: notes cannot be read", err=True)
    key = settings.service_api_key
    return create_app(
        diagnoser,
        examples=examples.load(cases, knowledge),
        api_key=key.get_secret_value() if key else None,
        max_concurrent=settings.service_max_concurrent,
        reader=reader,
    )


@app.command("serve")
def serve_http(
    host: Annotated[
        str, typer.Option(help="127.0.0.1: this machine only. 0.0.0.0: inside a container.")
    ] = "127.0.0.1",
    port: int = 8000,
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Serve the agent over HTTP: POST /v1/diagnose, its steps as a stream, and /docs."""
    import logging

    import uvicorn

    service = _service(data_dir, evals_dir)
    # The service's own log lines (one JSON line per answer), beside uvicorn's access log.
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    log = logging.getLogger("raredx.service")
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    logging.getLogger("mlflow").setLevel(logging.WARNING)
    uvicorn.run(service, host=host, port=port, log_level="info")


@app.command("demo")
def demo_page(
    api_url: Annotated[
        str, typer.Option(help="Where `raredx serve` is listening.")
    ] = "http://127.0.0.1:8000",
    host: str = "127.0.0.1",
    port: int = 8501,
) -> None:
    """Open the demo page (Streamlit) on a running `raredx serve`."""
    import importlib.util
    import os
    import sys

    if importlib.util.find_spec("streamlit") is None:
        _fail("streamlit is not installed — run `uv sync` (it is in the demo group)")
    page = Path(__file__).parent / "service" / "demo.py"
    command = [sys.executable, "-m", "streamlit", "run", str(page)]
    command += ["--server.address", host, "--server.port", str(port)]
    # No first-run prompt, and no usage statistics sent to Streamlit: nothing leaves.
    command += ["--server.headless", "true", "--browser.gatherUsageStats", "false"]
    command += ["--client.toolbarMode", "minimal"]  # no "Deploy" button: this page stays here
    # Streamlit takes this process's place, so a stop signal reaches it directly.
    os.execve(sys.executable, command, {**os.environ, "RAREDX_API_URL": api_url})


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

"""The `raredx` command line. Thin: every command calls into the package and prints."""

import functools
import hashlib
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

    from openai import OpenAI

    from raredx.evals.harness import Harness
    from raredx.knowledge.hpo import HPO
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


@data_app.command()
def build(data_dir: DataDir = settings.data_dir, evals_dir: EvalsDir = settings.evals_dir) -> None:
    """Parse the raw download into data/processed: one case per line."""
    source = _source(evals_dir)
    raw = sources.raw_dir(source, data_dir) / phenopackets.ARCHIVE
    if not raw.exists():
        _fail(f"{raw} missing — run `raredx data fetch` first")
    cases, skipped = phenopackets.load(raw)
    info = {
        "source": source.name,
        "version": source.version,
        "raw_sha256": source.files[phenopackets.ARCHIVE],
        "cases": len(cases),
        "skipped": dict(skipped),
    }
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


SYSTEMS = (
    "oracle",
    "popularity",
    "phenotype-rank",
    "rank-then-check",
    "similar-patients",
    "disease-texts",
    "gene-rank",
    "fixed-pipeline",
    "agent",
    "seeded-agent",
    "llm-direct",
    "llm-direct-thinking",
)


@functools.cache  # one release per process (hpo3 holds one ontology); load it once
def _knowledge(evals_dir: Path, data_dir: Path) -> "HPO":
    """The pinned HPO release, loaded; a clear message if it was never fetched."""
    from raredx.knowledge import hpo

    folder = sources.raw_dir(sources.load_sources(evals_dir / "datasets.toml")["hpo"], data_dir)
    if not (folder / "hp.obo").exists():
        _fail(f"{folder} has no HPO release — run `raredx data fetch hpo` first")
    return hpo.load(folder)


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
    from raredx.tools.search_disease_texts import SearchDiseaseTexts

    knowledge = _knowledge(evals_dir, data_dir)
    registry = sources.load_sources(evals_dir / "datasets.toml")
    folder = _text_index_dir(registry, data_dir, knowledge.release)
    if not (folder / INFO).exists():
        _fail(f"{folder} has no text index — run `raredx data index` first")
    index = TextIndex.load(folder, FastEmbedder(data_dir / "models"))
    return SearchDiseaseTexts(index, knowledge)


# Tools an agent can be given beyond the four core ones; --without leaves one out.
EXTRA_TOOLS = ("find_similar_patients", "search_disease_texts", "rank_candidate_genes")


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
) -> System:
    if name == "oracle":
        return Oracle.from_cases(cases)
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
    if name in ("agent", "seeded-agent"):
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
        if "search_disease_texts" not in without:
            extra.append(_text_search(evals_dir, data_dir))
        if with_genes and "rank_candidate_genes" not in without:
            from raredx.tools.rank_candidate_genes import RankCandidateGenes

            extra.append(RankCandidateGenes(knowledge))
        label = f"{name} (without {', '.join(without)})" if without else name
        return Agent(
            model,
            settings.llm_model,
            knowledge,
            seeded=name == "seeded-agent",
            extra_tools=extra,
            name=label,
        )
    if name in ("llm-direct", "llm-direct-thinking"):
        from raredx.baselines.llm_direct import LLMDirect

        return LLMDirect(
            _model_client(), settings.llm_model, thinking=name == "llm-direct-thinking"
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
    system: Annotated[str, typer.Option(help=" | ".join(SYSTEMS))],
    split: Annotated[str, typer.Option(help="Manifest to run on.")] = "dev-200",
    final: Annotated[bool, typer.Option(help="Required for heldout: the final run.")] = False,
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
    data_dir: DataDir = settings.data_dir,
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Evaluate a system on a manifest with MLflow; the run and every answer are recorded."""
    if split == "heldout" and not final:
        _fail("heldout is the final exam: run it once, with --final, when the design is frozen")
    left_out = tuple(sorted(set(without or [])))
    unknown = [t for t in left_out if t not in EXTRA_TOOLS]
    if unknown:
        _fail(f"--without takes {', '.join(EXTRA_TOOLS)}; not {', '.join(unknown)}")
    if left_out and system not in ("agent", "seeded-agent"):
        _fail("--without applies to the agents only")
    out_dir, cases = _processed(data_dir, evals_dir)
    manifest = _manifest(evals_dir, split)
    by_id = {c.id: c for c in cases}
    selected = [by_id[case_id] for case_id, _ in splits.read(manifest)]
    chosen = _system(system, cases, evals_dir, data_dir, similarity, left_out, with_genes)
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
    label, dataset_sha256, genes = split, manifest_sha256, None
    if with_genes:  # its own experiment and dataset: a different exam
        from raredx.evals import candidates

        knowledge = _knowledge(evals_dir, data_dir)
        genes = {c.id: candidates.candidate_genes(c, knowledge) for c in selected}
        label = f"{split}+genes"
        dataset_sha256 = hashlib.sha256(f"{manifest_sha256} {candidates.SPEC}".encode()).hexdigest()
        params |= {"label": label, "track": "phenotype+genes", "candidates": candidates.SPEC}
    from raredx.evals.harness import IncompleteRun

    harness = _harness()
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
        )
    except IncompleteRun as e:
        _fail(str(e))
    usage = harness.usage(run_id)
    tokens_in, tokens_out = usage["usage/input_tokens"], usage["usage/output_tokens"]
    cached = usage["usage/cached_input_tokens"]
    if tokens_in or tokens_out:
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
    if tokens_in or tokens_out:
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
    typer.echo(f"  sign test, two-sided: p = {scoring.sign_test(only_a, only_b):.3f}")


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

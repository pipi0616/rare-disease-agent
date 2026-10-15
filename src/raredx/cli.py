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

    from fastapi import FastAPI
    from openai import OpenAI

    from raredx.evals.harness import Harness
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
        for dataset in {splits.EXTERNAL.get(name, DATASET) for name in split}
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
    typer.echo(f"ok  {folder}: {', '.join([*splits.NAMES, *external])} pass every rule")


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
    "llm-direct",
    "llm-direct-thinking",
    "judge-table",
    "judge-review",
    "judge-table-thinking",
    "judge-review-thinking",
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


def _deeprare_queries(data_dir: Path) -> Path:
    from raredx.baselines.deeprare import QUERY_EMBEDDINGS

    return data_dir / "processed" / "deeprare" / QUERY_EMBEDDINGS


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
        # Off by default since chapter 20: on dev-200 the text search added nothing (4 cases
        # to 2 at top-1, p = 0.69) and cost 18% more tokens. --with-texts adds it back.
        if with_texts and "search_disease_texts" not in without:
            extra.append(_text_search(evals_dir, data_dir))
        if with_genes and "rank_candidate_genes" not in without:
            from raredx.tools.rank_candidate_genes import RankCandidateGenes

            extra.append(RankCandidateGenes(knowledge))
        label = name + (" (with search_disease_texts)" if with_texts else "")
        if without:
            label += f" (without {', '.join(without)})"
        return Agent(
            model,
            settings.llm_model,
            knowledge,
            seeded=name == "seeded-agent",
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
    if split.startswith("heldout") and not final:
        _fail("heldout is the final exam: run it once, with --final, when the design is frozen")
    if split in splits.EXTERNAL and not final:
        _fail(f"{split} tests the frozen system again: run it once, with --final")
    left_out = tuple(sorted(set(without or [])))
    unknown = [t for t in left_out if t not in EXTRA_TOOLS]
    if unknown:
        _fail(f"--without takes {', '.join(EXTRA_TOOLS)}; not {', '.join(unknown)}")
    if left_out and system not in ("agent", "seeded-agent"):
        _fail("--without applies to the agents only")
    if model and system not in ("llm-direct", "llm-direct-thinking"):
        _fail("--model applies to llm-direct only")
    if model and budget_usd is None:
        _fail("a run billed through OpenRouter needs a cap: give --budget-usd")
    # The systems are built on the pinned release (its design half fills the patient
    # bank) whatever the manifest; an external manifest's cases come from its own dataset.
    _, cases = _processed(data_dir, evals_dir)
    out_dir, asked = _processed(data_dir, evals_dir, splits.EXTERNAL.get(split, DATASET))
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
    evals_dir: EvalsDir = settings.evals_dir,
) -> None:
    """Score a recorded run again from its traces, as a new run. Nothing is re-asked."""
    harness = _harness()
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

    _, pool = _processed(data_dir, evals_dir, splits.EXTERNAL.get(split, DATASET))
    by_id = {c.id: c for c in pool}
    cases = [by_id[case_id] for case_id, _ in splits.read(_manifest(evals_dir, split))]
    harness = _harness()
    columns = {}
    for item in run:
        name, _, chain = item.partition("=")
        verdicts: dict[int, dict[str, bool]] = {k: {} for k in scoring.KS}
        lost: set[str] = set()
        for run_id in chain.split("+"):
            try:
                recorded = harness.client.get_run(run_id).data
            except MlflowException:
                _fail(f"{name}: no such run {run_id!r}")
            if recorded.tags.get("leak_audit") == "failed":
                _fail(f"{name}: run {run_id} failed its leak audit")
            answered = harness.hits(run_id, scoring.KS[0])
            lost = (lost - set(answered)) | set(harness.lost_cases(run_id))
            for k in scoring.KS:
                verdicts[k] |= harness.hits(run_id, k)
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

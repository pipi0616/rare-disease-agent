"""Evaluation manifests: which cases each evaluation runs on, frozen in git.

A manifest is a TSV of case_id and pmid. The cases themselves stay out of git;
the manifest is what makes "the dev set" mean the same cases for everyone,
forever. Six come from the pinned release:

    design              every design-split case         confirming a change at full size
    dev-200             200 design cases, one/paper     day-to-day iteration
    ci-20               20 of dev-200                   the regression check in CI
    heldout             every held-out case             the full held-out set
    heldout-papers      one case per held-out paper     the final run, once
    heldout-papers-200  200 of heldout-papers           comparisons billed per case

and five come from outside it:

    temporal-2026-10       one case per paper first public on or after CUTOFF   temporal test
    rarebench-hms          every HMS patient of RareBench                        practice
    rarebench-ramedis      every RAMEDIS patient of RareBench                    practice
    rarebench-ramedis-200  200 of rarebench-ramedis                              practice
    rarebench-mme          every MME patient of RareBench                        external test

HMS and RAMEDIS tested v1.0 once, after it was frozen; it lost to the bare model
there, and they have been practice sets since (PRACTICE).

The final run takes one case from every held-out paper, as dev-200 does from the
design split and for the same reason; it is the held-out set at the dev set's grain.
heldout-papers-200 is a fixed random fifth of it, for systems paid for by the case
(other providers' models): every system already run on heldout-papers has its
answers to these 200 recorded, so a comparison on them costs only the new system.

dev-200 takes at most one case per paper. The largest paper contributes 462
cases; sampling cases rather than papers would fill the dev set with one
family's presentation and measure the same question many times over.

Manifests are frozen: `make_all` refuses to change one that already exists
unless forced, and a forced change should be a new, deliberately named version.
"""

import random
from collections import defaultdict
from datetime import date
from pathlib import Path

from raredx.data.cases import Case

SEED = 20261008
DEV_SIZE = 200
CI_SIZE = 20
HELDOUT_SEED = SEED + 1
HELDOUT_SAMPLE = 200
NAMES = ("design", "dev-200", "ci-20", "heldout", "heldout-papers", "heldout-papers-200")
HEADER = "case_id\tpmid"

Row = tuple[str, str]


class FrozenManifestError(Exception):
    pass


def paper(case: Case) -> str:
    """What sampling counts as one report: the case's paper; a case with none, itself."""
    return case.pmid or case.id


def sample_dev(design_cases: list[Case], n: int = DEV_SIZE, seed: int = SEED) -> list[Case]:
    """n design cases from n different papers, chosen by a fixed seed."""
    by_paper: dict[str, list[Case]] = defaultdict(list)
    for case in design_cases:
        by_paper[paper(case)].append(case)
    rng = random.Random(seed)
    papers = rng.sample(sorted(by_paper), n)
    return [rng.choice(sorted(by_paper[p], key=lambda c: c.id)) for p in papers]


def sample_per_paper(cases: list[Case], seed: int = HELDOUT_SEED) -> list[Case]:
    """One case from every paper, chosen by a fixed seed."""
    by_paper: dict[str, list[Case]] = defaultdict(list)
    for case in cases:
        by_paper[paper(case)].append(case)
    rng = random.Random(seed)
    return [rng.choice(sorted(by_paper[p], key=lambda c: c.id)) for p in sorted(by_paper)]


def build(cases: list[Case]) -> dict[str, list[Row]]:
    design = [c for c in cases if c.split == "design"]
    heldout = [c for c in cases if c.split == "heldout"]
    dev = sample_dev(design)
    ci = random.Random(SEED).sample(sorted(dev, key=lambda c: c.id), CI_SIZE)

    def rows(selected: list[Case]) -> list[Row]:
        return sorted((c.id, c.pmid or "") for c in selected)

    per_paper = sorted(sample_per_paper(heldout), key=lambda c: c.id)
    sample = random.Random(HELDOUT_SEED + 1).sample(per_paper, min(HELDOUT_SAMPLE, len(per_paper)))
    return {
        "design": rows(design),
        "dev-200": rows(dev),
        "ci-20": rows(ci),
        "heldout": rows(heldout),
        "heldout-papers": rows(per_paper),
        "heldout-papers-200": rows(sample),
    }


def render(rows: list[Row]) -> str:
    return HEADER + "\n" + "".join(f"{case_id}\t{pmid}\n" for case_id, pmid in rows)


def read(path: Path) -> list[Row]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != HEADER:
        raise ValueError(f"{path}: expected header {HEADER!r}")
    rows: list[Row] = []
    for line in lines[1:]:
        case_id, pmid = line.split("\t")
        rows.append((case_id, pmid))
    return rows


def make_all(cases: list[Case], splits_dir: Path, *, force: bool = False) -> dict[str, str]:
    """Write the manifests, or confirm they are unchanged. Checks all before writing any."""
    return _write_frozen(
        {name: render(rows) for name, rows in build(cases).items()}, splits_dir, force
    )


def _write_frozen(built: dict[str, str], splits_dir: Path, force: bool) -> dict[str, str]:
    status: dict[str, str] = {}
    for name, text in built.items():
        path = splits_dir / f"{name}.tsv"
        if not path.exists():
            status[name] = "written"
        elif path.read_text(encoding="utf-8") == text:
            status[name] = "unchanged"
        elif force:
            status[name] = "replaced"
        else:
            raise FrozenManifestError(
                f"{path} would change. Manifests are frozen: create a new, deliberately "
                "named version instead, or pass --force and say why in the commit."
            )
    splits_dir.mkdir(parents=True, exist_ok=True)
    for name, text in built.items():
        if status[name] != "unchanged":
            (splits_dir / f"{name}.tsv").write_text(text, encoding="utf-8")
    return status


def check(splits_dir: Path) -> list[str]:
    """Rules the manifests must satisfy on their own. Needs no data, so CI runs it."""
    missing = [n for n in NAMES if not (splits_dir / f"{n}.tsv").exists()]
    if missing:
        return [f"missing manifest: {n}.tsv" for n in missing]
    m = {n: read(splits_dir / f"{n}.tsv") for n in NAMES}
    ids = {n: {case_id for case_id, _ in rows} for n, rows in m.items()}
    papers = {n: {pmid for _, pmid in rows} for n, rows in m.items()}

    problems = [f"{n}: a case is listed twice" for n, rows in m.items() if len(ids[n]) != len(rows)]
    if ids["design"] & ids["heldout"]:
        problems.append("a case is in both design and heldout")
    if papers["design"] & papers["heldout"]:
        problems.append("a paper has cases in both design and heldout")
    if not ids["dev-200"] <= ids["design"]:
        problems.append("dev-200 contains cases that are not in design")
    if not ids["ci-20"] <= ids["dev-200"]:
        problems.append("ci-20 contains cases that are not in dev-200")
    if len(m["dev-200"]) != DEV_SIZE:
        problems.append(f"dev-200 has {len(m['dev-200'])} cases, expected {DEV_SIZE}")
    if len(papers["dev-200"]) != len(m["dev-200"]):
        problems.append("dev-200 has more than one case from the same paper")
    if len(m["ci-20"]) != CI_SIZE:
        problems.append(f"ci-20 has {len(m['ci-20'])} cases, expected {CI_SIZE}")
    if not ids["heldout-papers"] <= ids["heldout"]:
        problems.append("heldout-papers contains cases that are not in heldout")
    if len(papers["heldout-papers"]) != len(m["heldout-papers"]):
        problems.append("heldout-papers has more than one case from the same paper")
    if papers["heldout-papers"] != papers["heldout"]:
        problems.append("heldout-papers does not cover every held-out paper")
    if not ids["heldout-papers-200"] <= ids["heldout-papers"]:
        problems.append("heldout-papers-200 contains cases that are not in heldout-papers")
    expected = min(HELDOUT_SAMPLE, len(m["heldout-papers"]))
    if len(m["heldout-papers-200"]) != expected:
        problems.append(
            f"heldout-papers-200 has {len(m['heldout-papers-200'])} cases, expected {expected}"
        )
    return problems


def check_against(cases: list[Case], splits_dir: Path) -> list[str]:
    """Rules that need the data: every listed case exists, and the splits are complete."""
    by_id = {c.id: c for c in cases}
    problems = []
    for name in NAMES:
        for case_id, pmid in read(splits_dir / f"{name}.tsv"):
            if case_id not in by_id:
                problems.append(f"{name}: {case_id} is not in the dataset")
            elif (by_id[case_id].pmid or "") != pmid:
                problems.append(
                    f"{name}: {case_id} has pmid {by_id[case_id].pmid}, manifest says {pmid}"
                )
    for split in ("design", "heldout"):
        listed = {case_id for case_id, _ in read(splits_dir / f"{split}.tsv")}
        actual = {c.id for c in cases if c.split == split}
        if listed != actual:
            problems.append(f"{split}.tsv does not list exactly the {split} cases of the dataset")
    return problems


# ── testing v1.0 again: cases from outside the pinned release ──────
#
# Temporal: the held-out half can still have been read by the model while it was
# trained, so a score on it may owe something to memory. A paper first public after
# the model's training data ends cannot have been: one case from each such paper the
# systems were never developed on — the held-out half (the very case heldout-papers
# asks) and the papers the store added after the pinned release (one case each, by a
# fixed seed). Design papers never: they were developed on, and fill the patient bank.
#
# External: patients from other sources than Phenopacket Store, curated by other
# people. RareBench's HMS and RAMEDIS; LIRICAL is left out (rarebench.py). MME, left
# out at first too, is the external test of the hypothesis agent: no system had run on
# it when HMS and RAMEDIS became practice sets.

TEMPORAL = "temporal-2026-10"
# deepseek-flash, the model inside every system here, is reported to have been
# trained on data up to May 2025. DeepSeek publishes no date: the figure is third-party
# (docs/temporal_plan.md), and a month's margin would not change which papers count.
CUTOFF = date(2025, 6, 1)
TEMPORAL_SEED = SEED + 3
RAMEDIS_SEED = SEED + 4
RAMEDIS_SAMPLE = 200
RAREBENCH_SETS = {
    "rarebench-hms": "HMS",
    "rarebench-ramedis": "RAMEDIS",
    "rarebench-mme": "MME",
}
# manifest -> the registered dataset its cases are read from
EXTERNAL: dict[str, str] = {
    TEMPORAL: "phenopacket-store-snapshot",
    "rarebench-hms": "rarebench",
    "rarebench-ramedis": "rarebench",
    "rarebench-ramedis-200": "rarebench",
    "rarebench-mme": "rarebench",
}
# External sets developed on since v1.0 lost there (its errors were read to find why):
# run any number of times, and no longer a test of anything.
PRACTICE = frozenset({"rarebench-hms", "rarebench-ramedis", "rarebench-ramedis-200"})


def temporal(
    snapshot: list[Case],
    heldout_papers: list[Row],
    dates: dict[str, date],
    cutoff: date = CUTOFF,
) -> list[Row]:
    """One case per paper first public on or after the cutoff that no system was
    developed on. A paper without a known date is left out."""

    def after(pmid: str | None) -> bool:
        return pmid is not None and dates.get(pmid, date.min) >= cutoff

    present = {c.id for c in snapshot}
    rows = [
        (case_id, pmid) for case_id, pmid in heldout_papers if after(pmid) and case_id in present
    ]
    new = [c for c in snapshot if c.split == "external" and after(c.pmid)]
    rows += [(c.id, c.pmid or "") for c in sample_per_paper(new, TEMPORAL_SEED)]
    return sorted(rows)


def build_external(
    snapshot: list[Case], rarebench: list[Case], heldout_papers: list[Row], dates: dict[str, date]
) -> dict[str, list[Row]]:
    sets = {
        name: sorted((c.id, "") for c in rarebench if c.cohort == cohort)
        for name, cohort in RAREBENCH_SETS.items()
    }
    ramedis = sets["rarebench-ramedis"]
    sample = random.Random(RAMEDIS_SEED).sample(ramedis, min(RAMEDIS_SAMPLE, len(ramedis)))
    return {
        TEMPORAL: temporal(snapshot, heldout_papers, dates),
        **sets,
        "rarebench-ramedis-200": sorted(sample),
    }


def make_external(
    snapshot: list[Case],
    rarebench: list[Case],
    dates: dict[str, date],
    splits_dir: Path,
    *,
    force: bool = False,
) -> dict[str, str]:
    """Write the four external manifests, or confirm they are unchanged; frozen like the rest."""
    heldout_papers = read(splits_dir / "heldout-papers.tsv")
    built = build_external(snapshot, rarebench, heldout_papers, dates)
    return _write_frozen({n: render(rows) for n, rows in built.items()}, splits_dir, force)


def check_external(splits_dir: Path, dates: dict[str, date] | None = None) -> list[str]:
    """Rules the external manifests keep on their own, when they exist; no case data
    needed, so CI runs it. `dates`: the papers' first public days, from git."""
    present = [n for n in EXTERNAL if (splits_dir / f"{n}.tsv").exists()]
    if not present:
        return []
    if len(present) < len(EXTERNAL):
        return [f"missing manifest: {n}.tsv" for n in EXTERNAL if n not in present]
    m = {n: read(splits_dir / f"{n}.tsv") for n in EXTERNAL}
    problems = [
        f"{n}: a case is listed twice"
        for n, rows in m.items()
        if len({r[0] for r in rows}) != len(rows)
    ]
    design = {pmid for _, pmid in read(splits_dir / "design.tsv")}
    heldout_papers = set(read(splits_dir / "heldout-papers.tsv"))
    heldout = {pmid for _, pmid in heldout_papers}
    papers = [pmid for _, pmid in m[TEMPORAL]]
    if len(set(papers)) != len(papers) or "" in papers:
        problems.append(f"{TEMPORAL}: not exactly one case per paper")
    if set(papers) & design:
        problems.append(f"{TEMPORAL}: a design paper is in it")
    if any(
        pmid in heldout and row not in heldout_papers for row in m[TEMPORAL] for pmid in [row[1]]
    ):
        problems.append(f"{TEMPORAL}: a held-out paper with another case than heldout-papers asks")
    if dates is not None and any(dates.get(p, date.min) < CUTOFF for p in papers):
        problems.append(f"{TEMPORAL}: a paper first public before {CUTOFF}")
    for name, cohort in RAREBENCH_SETS.items():
        if any(not case_id.startswith(f"RareBench_{cohort}_") for case_id, _ in m[name]):
            problems.append(f"{name}: a case from another set")
    ramedis, sample = set(m["rarebench-ramedis"]), m["rarebench-ramedis-200"]
    if not set(sample) <= ramedis:
        problems.append("rarebench-ramedis-200 contains cases that are not in rarebench-ramedis")
    if len(sample) != min(RAMEDIS_SAMPLE, len(ramedis)):
        problems.append(f"rarebench-ramedis-200 has {len(sample)} cases")
    return problems


def check_external_against(
    snapshot: list[Case], rarebench: list[Case], dates: dict[str, date], splits_dir: Path
) -> list[str]:
    """Rules that need the data: built again from it, every external manifest is the same."""
    built = build_external(snapshot, rarebench, read(splits_dir / "heldout-papers.tsv"), dates)
    return [
        f"{name}.tsv is not what its data and rules give"
        for name, rows in built.items()
        if read(splits_dir / f"{name}.tsv") != rows
    ]

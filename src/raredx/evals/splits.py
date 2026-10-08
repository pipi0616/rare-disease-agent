"""Evaluation manifests: which cases each evaluation runs on, frozen in git.

A manifest is a TSV of case_id and pmid. The cases themselves stay out of git;
the manifest is what makes "the dev set" mean the same cases for everyone,
forever. There are four:

    design   every design-split case       confirming a change at full size
    dev-200  200 design cases, one/paper   day-to-day iteration
    ci-20    20 of dev-200                 the regression check in CI
    heldout  every held-out case           the final run, once

dev-200 takes at most one case per paper. The largest paper contributes 462
cases; sampling cases rather than papers would fill the dev set with one
family's presentation and measure the same question many times over.

Manifests are frozen: `make_all` refuses to change one that already exists
unless forced, and a forced change should be a new, deliberately named version.
"""

import random
from collections import defaultdict
from pathlib import Path

from raredx.data.cases import Case

SEED = 20261008
DEV_SIZE = 200
CI_SIZE = 20
NAMES = ("design", "dev-200", "ci-20", "heldout")
HEADER = "case_id\tpmid"

Row = tuple[str, str]


class FrozenManifestError(Exception):
    pass


def sample_dev(design_cases: list[Case], n: int = DEV_SIZE, seed: int = SEED) -> list[Case]:
    """n design cases from n different papers, chosen by a fixed seed."""
    by_paper: dict[str, list[Case]] = defaultdict(list)
    for case in design_cases:
        by_paper[case.pmid].append(case)
    rng = random.Random(seed)
    papers = rng.sample(sorted(by_paper), n)
    return [rng.choice(sorted(by_paper[p], key=lambda c: c.id)) for p in papers]


def build(cases: list[Case]) -> dict[str, list[Row]]:
    design = [c for c in cases if c.split == "design"]
    heldout = [c for c in cases if c.split == "heldout"]
    dev = sample_dev(design)
    ci = random.Random(SEED).sample(sorted(dev, key=lambda c: c.id), CI_SIZE)

    def rows(selected: list[Case]) -> list[Row]:
        return sorted((c.id, c.pmid) for c in selected)

    return {
        "design": rows(design),
        "dev-200": rows(dev),
        "ci-20": rows(ci),
        "heldout": rows(heldout),
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
    built = {name: render(rows) for name, rows in build(cases).items()}
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
    return problems


def check_against(cases: list[Case], splits_dir: Path) -> list[str]:
    """Rules that need the data: every listed case exists, and the splits are complete."""
    by_id = {c.id: c for c in cases}
    problems = []
    for name in NAMES:
        for case_id, pmid in read(splits_dir / f"{name}.tsv"):
            if case_id not in by_id:
                problems.append(f"{name}: {case_id} is not in the dataset")
            elif by_id[case_id].pmid != pmid:
                problems.append(
                    f"{name}: {case_id} has pmid {by_id[case_id].pmid}, manifest says {pmid}"
                )
    for split in ("design", "heldout"):
        listed = {case_id for case_id, _ in read(splits_dir / f"{split}.tsv")}
        actual = {c.id for c in cases if c.split == split}
        if listed != actual:
            problems.append(f"{split}.tsv does not list exactly the {split} cases of the dataset")
    return problems

"""Manifests: sampling, freezing, and the rules they must keep.

The synthetic store has 300 design papers and 100 held-out papers with one to
three cases each, enough for a 200-paper dev set. The last test checks the
manifests committed in evals/splits; it needs no data, so it runs in CI.
"""

from pathlib import Path

import pytest

from raredx.data.cases import Case
from raredx.evals import splits

COMMITTED = Path(__file__).resolve().parents[2] / "evals" / "splits"


def case(case_id: str, pmid: str, split: str) -> Case:
    return Case.model_validate(
        {
            "id": case_id,
            "cohort": "X",
            "hpo_ids": ["HP:0000001"],
            "hpo_labels": ["All"],
            "disease_id": "OMIM:100000",
            "disease_label": "Disease",
            "gene": "GENE",
            "variants": [],
            "pmid": pmid,
            "sex": None,
            "split": split,
        }
    )


@pytest.fixture
def store() -> list[Case]:
    cases = []
    for paper in range(400):
        split = "design" if paper < 300 else "heldout"
        for i in range(1 + paper % 3):
            cases.append(case(f"PMID_{paper}_{i}", f"PMID:{paper}", split))
    return cases


def test_dev_takes_one_case_per_paper_from_design_only(store: list[Case]) -> None:
    design = [c for c in store if c.split == "design"]
    dev = splits.sample_dev(design)
    assert len(dev) == splits.DEV_SIZE
    assert len({c.pmid for c in dev}) == splits.DEV_SIZE
    assert all(c.split == "design" for c in dev)


def test_the_final_run_takes_one_case_from_every_heldout_paper(store: list[Case]) -> None:
    heldout = [c for c in store if c.split == "heldout"]
    sample = splits.sample_per_paper(heldout)
    assert {c.pmid for c in sample} == {c.pmid for c in heldout}
    assert len(sample) == 100 and all(c.split == "heldout" for c in sample)
    assert sample == splits.sample_per_paper(list(reversed(heldout)))  # fixed by the seed


def test_sampling_is_fixed_by_the_seed(store: list[Case]) -> None:
    assert splits.build(store) == splits.build(list(reversed(store)))


def test_make_all_writes_once_then_reports_unchanged(store: list[Case], tmp_path: Path) -> None:
    assert set(splits.make_all(store, tmp_path).values()) == {"written"}
    assert set(splits.make_all(store, tmp_path).values()) == {"unchanged"}
    assert splits.check(tmp_path) == []
    assert splits.check_against(store, tmp_path) == []


def test_a_frozen_manifest_is_not_overwritten(store: list[Case], tmp_path: Path) -> None:
    splits.make_all(store, tmp_path)
    before = (tmp_path / "dev-200.tsv").read_text()
    changed = store + [case("PMID_999_0", "PMID:999", "design")]
    with pytest.raises(splits.FrozenManifestError):
        splits.make_all(changed, tmp_path)
    assert (tmp_path / "dev-200.tsv").read_text() == before


def test_check_catches_a_heldout_case_moved_into_dev(store: list[Case], tmp_path: Path) -> None:
    splits.make_all(store, tmp_path)
    case_id, pmid = splits.read(tmp_path / "heldout.tsv")[0]
    with (tmp_path / "dev-200.tsv").open("a") as f:
        f.write(f"{case_id}\t{pmid}\n")
    problems = splits.check(tmp_path)
    assert "dev-200 contains cases that are not in design" in problems
    assert any("expected 200" in p for p in problems)


def test_committed_manifests_keep_every_rule() -> None:
    assert splits.check(COMMITTED) == []


def test_the_billed_sample_is_a_fixed_part_of_the_final_run(store: list[Case]) -> None:
    built = splits.build(store)
    sample, every = built["heldout-papers-200"], built["heldout-papers"]
    assert set(sample) <= set(every)
    assert len(sample) == min(splits.HELDOUT_SAMPLE, len(every))  # 100 papers here: all of them
    assert sample == splits.build(list(reversed(store)))["heldout-papers-200"]


# ── the external manifests ──────────────────────────────────────────

EVALS = COMMITTED.parent


def rarebench_case(cohort: str, i: int) -> Case:
    patient = case(f"RareBench_{cohort}_{i:03d}", "", "external")
    return patient.model_copy(update={"pmid": None, "cohort": cohort})


@pytest.fixture
def snapshot(store: list[Case]) -> list[Case]:
    """The store later on: two new papers (1000, 1001), the second with two cases."""
    new = [case("PMID_1000_0", "PMID:1000", "external")]
    new += [case(f"PMID_1001_{i}", "PMID:1001", "external") for i in range(2)]
    return store + new


def test_the_temporal_test_takes_late_papers_no_system_was_developed_on(
    store: list[Case], snapshot: list[Case]
) -> None:
    from datetime import date

    built = splits.build(store)
    late = date(2026, 1, 1)
    # design paper 0, held-out papers 300 and 301, new papers 1000 and 1001; 301 too early
    dates = {f"PMID:{p}": late for p in (0, 300, 1000, 1001)} | {"PMID:301": date(2020, 1, 1)}
    rows = splits.temporal(snapshot, built["heldout-papers"], dates)
    assert {pmid for _, pmid in rows} == {"PMID:300", "PMID:1000", "PMID:1001"}
    assert next(r for r in rows if r[1] == "PMID:300") in built["heldout-papers"]  # the same case
    assert rows == splits.temporal(list(reversed(snapshot)), built["heldout-papers"], dates)


def test_external_manifests_are_written_once_and_keep_their_rules(
    store: list[Case], snapshot: list[Case], tmp_path: Path
) -> None:
    from datetime import date

    splits.make_all(store, tmp_path)
    rarebench = [rarebench_case("HMS", i) for i in range(1, 4)]
    rarebench += [rarebench_case("RAMEDIS", i) for i in range(1, 301)]
    dates = {"PMID:1000": date(2026, 1, 1)}
    status = splits.make_external(snapshot, rarebench, dates, tmp_path)
    assert set(status.values()) == {"written"}
    assert (
        splits.make_external(snapshot, rarebench, dates, tmp_path)["rarebench-hms"] == "unchanged"
    )
    assert splits.check_external(tmp_path, dates) == []
    assert splits.check_external_against(snapshot, rarebench, dates, tmp_path) == []
    assert len(splits.read(tmp_path / "rarebench-ramedis-200.tsv")) == 200
    # a design paper slipped into the temporal test is caught
    with (tmp_path / f"{splits.TEMPORAL}.tsv").open("a") as f:
        f.write("PMID_0_0\tPMID:0\n")
    assert f"{splits.TEMPORAL}: a design paper is in it" in splits.check_external(tmp_path)


def test_committed_external_manifests_keep_every_rule() -> None:
    from raredx.data import pubmed

    assert all((COMMITTED / f"{name}.tsv").exists() for name in splits.EXTERNAL)
    assert splits.check_external(COMMITTED, pubmed.read(EVALS / "pubmed_dates.tsv")) == []

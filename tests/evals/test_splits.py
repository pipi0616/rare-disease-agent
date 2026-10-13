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

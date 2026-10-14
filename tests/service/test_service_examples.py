"""The listed examples against the manifests in git: no data needed."""

from pathlib import Path

from raredx.evals import splits
from raredx.service import examples

EVALS = Path(__file__).resolve().parents[2] / "evals"


def test_every_example_is_a_case_of_the_heldout_sample() -> None:
    heldout = {case_id for case_id, _ in splits.read(EVALS / "splits" / "heldout-papers.tsv")}
    listed = examples.listed()
    assert len(listed) == 5
    assert {case_id for case_id, _, _ in listed} <= heldout
    assert all(title and note.endswith(".") for _, title, note in listed)

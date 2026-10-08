"""The processed layer: cases written and read back unchanged."""

from pathlib import Path

from raredx.data import cases as case_store
from raredx.data.cases import Case, Variant


def make_case(case_id: str, gene: str | None = "DAP3") -> Case:
    return Case(
        id=case_id,
        cohort="DAP3",
        hpo_ids=["HP:0000786", "HP:0008209"],
        hpo_labels=["Primary amenorrhea", "Premature ovarian insufficiency"],
        disease_id="OMIM:621101",
        disease_label="Perrault syndrome 7",
        gene=gene,
        variants=[Variant(gene=gene)] if gene else [],
        pmid="PMID:39701103",
        sex="FEMALE",
        split="design",
    )


def test_cases_round_trip_sorted_with_build_info(tmp_path: Path) -> None:
    original = [make_case("PMID_2_b"), make_case("PMID_1_a", gene=None)]
    case_store.write(original, tmp_path, {"source": "test", "cases": 2})

    assert case_store.read(tmp_path) == sorted(original, key=lambda c: c.id)
    assert case_store.read_build_info(tmp_path) == {"source": "test", "cases": 2}

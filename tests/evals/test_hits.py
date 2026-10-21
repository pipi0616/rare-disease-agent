"""The per-case table paired comparisons read, on the test HPO release."""

from collections.abc import Callable
from pathlib import Path

import pytest

from raredx.data.cases import Case
from raredx.evals import hits
from raredx.knowledge.hpo import HPO


def test_a_case_is_answerable_unless_masking_or_the_release_rules_it_out(
    hpo: HPO, make_case: Callable[..., Case]
) -> None:
    assert hits.answerable(make_case("a", disease_id="OMIM:690001", pmid="PMID:7"), hpo)
    # known only from the case's own paper: the mask makes it not exist
    assert not hits.answerable(make_case("b", disease_id="OMIM:690004", pmid="PMID:1004"), hpo)
    # from another paper, the same disease is there to be found
    assert hits.answerable(make_case("c", disease_id="OMIM:690004", pmid="PMID:7"), hpo)
    # not a disease of the release, unless an accepted alternative is
    clinic = make_case("d", disease_id="ORPHA:81", pmid=None, split="external")
    assert not hits.answerable(clinic, hpo)
    also = clinic.model_copy(update={"also_accepted": ["OMIM:690003"]})
    assert hits.answerable(also, hpo)


def test_the_table_puts_runs_side_by_side_and_reads_back(
    hpo: HPO, make_case: Callable[..., Case], tmp_path: Path
) -> None:
    cases = [make_case("1", disease_id="OMIM:690001"), make_case("2", disease_id="OMIM:690004")]
    run = {k: {"1": True, "2": k == 10, "9": True} for k in (1, 3, 5, 10)}  # answered more
    rows = hits.table(cases, {"agent": run}, hpo)
    assert [r["agent@1"] for r in rows] == ["1", "0"] and rows[1]["agent@10"] == "1"
    hits.write(rows, tmp_path / "t.tsv")
    assert hits.read(tmp_path / "t.tsv") == rows
    with pytest.raises(ValueError, match="no answer to 1"):
        hits.table([*cases, make_case("3")], {"agent": run}, hpo)


def test_a_run_and_its_fill_ins_make_one_column() -> None:
    def verdicts(**hit: bool) -> hits.Verdicts:
        return {k: dict(hit) for k in (1, 3, 5, 10)}

    first = (verdicts(a=True, b=False, c=False), {"b", "c"})  # b and c lost to the API
    again = (verdicts(b=True, c=False), {"c"})  # b answered, c lost again
    last: tuple[hits.Verdicts, set[str]] = (verdicts(c=True), set())
    merged, lost = hits.combine([first, again])
    assert merged[1] == {"a": True, "b": True, "c": False} and lost == {"c"}
    merged, lost = hits.combine([first, again, last])
    assert merged[1] == {"a": True, "b": True, "c": True} and lost == set()


def test_with_identity_an_orphanet_diagnosis_is_answerable_through_its_disease(
    knowledge: HPO, make_case: Callable[..., Case]
) -> None:
    merged = make_case("e", disease_id="ORPHA:9001", pmid=None, split="external")
    assert hits.answerable(merged, knowledge)  # merged into OMIM:690001
    own = make_case("f", disease_id="ORPHA:9002", pmid=None, split="external")
    assert hits.answerable(own, knowledge)
    # hidden with its OMIM disease when that is known only from the case's own paper
    hidden = make_case("g", disease_id="ORPHA:9004", pmid="PMID:1004")
    assert not hits.answerable(hidden, knowledge)

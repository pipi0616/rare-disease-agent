"""The HPO release in memory, on a miniature of the real files (tests/fixtures/hpo)."""

import shutil
from pathlib import Path
from typing import Any

import pytest

from raredx.knowledge import hpo as hpo_module
from raredx.knowledge.hpo import HPO, Frequency, absent, frequency

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "hpo"


def terms(hpo_set: Any) -> set[str]:
    return {term.id for term in hpo_set}


def profiles(hpo: HPO, masked: frozenset[str] = frozenset()) -> dict[str, set[str]]:
    return {d: terms(p) for d, p in zip(hpo.disease_ids, hpo.profiles(masked), strict=True)}


def test_the_release_is_the_one_hp_obo_declares(hpo: HPO) -> None:
    assert hpo.release == hpo_module.release_of(FIXTURE) == "2099-01-01"


def test_a_profile_holds_an_omim_diseases_phenotype_and_nothing_else(hpo: HPO) -> None:
    assert hpo.disease_ids == [f"OMIM:69000{i}" for i in range(1, 6)]  # no Orphanet entry
    found = profiles(hpo)
    assert found["OMIM:690001"] == {"HP:0000407", "HP:0000786"}  # not its inheritance
    assert found["OMIM:690002"] == {"HP:0000407", "HP:0000510"}  # not the NOT line


def test_a_sign_looked_for_and_never_found_is_not_in_the_profile(hpo: HPO) -> None:
    # OMIM:690003 lists hearing impairment at 0/4: absent in all four patients.
    assert profiles(hpo)["OMIM:690003"] == {"HP:0001250"}
    assert profiles(hpo)["OMIM:690005"] == {"HP:0000407", "HP:0000510", "HP:0001250"}


def test_genes_are_the_mendelian_ones(hpo: HPO) -> None:
    assert hpo.genes == {
        "OMIM:690001": ("GENEA",),
        "OMIM:690002": ("GENEB1", "GENEB2"),
        "OMIM:690005": ("GENEE",),
        "OMIM:699998": ("GENEF",),  # a disease with no phenotype annotation
    }  # and OMIM:690004's gene "-" (no symbol) is not a gene


def test_a_genes_diseases_are_those_with_phenotype_annotations(hpo: HPO) -> None:
    assert hpo.diseases_of_gene == {
        "GENEA": ("OMIM:690001",),
        "GENEB1": ("OMIM:690002",),
        "GENEB2": ("OMIM:690002",),
        "GENEE": ("OMIM:690005",),
    }  # GENEF's only disease has no annotation: nothing can be said about it


def test_masking_a_paper_removes_only_what_rests_on_it_alone(hpo: HPO) -> None:
    masked = profiles(hpo, frozenset({"PMID:1002"}))
    # HP:0000510 is also supported by OMIM's own entry, so it stays; HP:0000407 goes.
    assert masked["OMIM:690002"] == {"HP:0000510"}
    assert masked["OMIM:690001"] == profiles(hpo)["OMIM:690001"]
    assert hpo.cites("OMIM:690002", "PMID:1002") and not hpo.cites("OMIM:690001", "PMID:1002")


def test_a_diseases_sources_are_the_references_its_annotation_cites(hpo: HPO) -> None:
    assert hpo.references("OMIM:690002") == {"PMID:1002", "OMIM:690002"}
    assert hpo.references("OMIM:999999") == set()


def test_a_patients_terms_are_cleaned_and_unknown_ones_reported(hpo: HPO) -> None:
    patient, unknown = hpo.patient(
        ["HP:0000365", "HP:0000407", "HP:0099999", "HP:0000007", "HP:0123456"]
    )
    # Hearing impairment gives way to the more specific term below it; the obsolete
    # term is replaced (by that same term); an inheritance mode is not a sign.
    assert terms(patient) == {"HP:0000407"}
    assert unknown == ["HP:0123456"]


def test_a_second_release_in_the_same_process_is_refused(hpo: HPO, tmp_path: Path) -> None:
    other = tmp_path / "hpo"
    shutil.copytree(FIXTURE, other)
    obo = other / "hp.obo"
    obo.write_text(obo.read_text().replace("2099-01-01", "2099-02-01"))
    with pytest.raises(hpo_module.WrongRelease):
        hpo_module.load(other)


def test_every_aspect_is_kept_and_masked_line_by_line(hpo: HPO) -> None:
    assert [x.term for x in hpo.lines("OMIM:690005", "I")] == ["HP:0000007"]
    assert [x.term for x in hpo.lines("OMIM:690005", "C")] == ["HP:0003577"]
    masked = hpo.lines("OMIM:690005", "P", frozenset({"PMID:1005"}))
    assert [(x.term, x.frequency) for x in masked] == [("HP:0000407", "1/4")]


def test_a_term_is_named_and_an_obsolete_one_replaced(hpo: HPO) -> None:
    assert hpo.term("HP:0000407")[:2] == ("HP:0000407", "Sensorineural hearing impairment")
    assert hpo.term("HP:0099999")[0] == "HP:0000407"


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        (["3/4", "1/4"], Frequency(0.5, "4/8")),  # counts from two sources pool
        (["2/2", "0/3"], Frequency(0.4, "2/5")),  # a source that never saw it still counts
        (["HP:0040282"], Frequency(0.545, "frequent (30–79%)")),
        (["25%"], Frequency(0.25, "25%")),
        (["", "1/2"], Frequency(0.5, "1/2")),
        ([""], Frequency(None, None)),
        (["0/3", "0/2"], Frequency(0.0, "0/5")),  # looked for in five patients, none had it
        (["0/3", ""], Frequency(None, None)),  # another source says it occurs, not how often
    ],
)
def test_a_frequency_is_read_from_however_it_was_written(
    written: list[str], expected: Frequency
) -> None:
    assert frequency(written) == expected


def test_several_frequency_terms_average() -> None:
    fraction, text = frequency(["HP:0040281", "HP:0040283"])
    assert fraction == pytest.approx((0.895 + 0.17) / 2) and text == "about 53%"


@pytest.mark.parametrize(
    ("written", "is_absent"),
    [("0/5", True), ("0%", True), ("HP:0040285", True), ("1/5", False), ("", False)],
)
def test_absent_means_looked_for_and_not_found(written: str, is_absent: bool) -> None:
    assert absent(written) is is_absent


def test_a_diseases_features_gather_every_line_about_each(hpo: HPO) -> None:
    found = {f.term: f for f in hpo.features("OMIM:690005")}
    assert set(found) == {"HP:0000407", "HP:0000510", "HP:0001250", "HP:0000786"}
    assert found["HP:0000407"].frequency == Frequency(0.5, "4/8")
    assert found["HP:0000407"].sources == {"PMID:1005", "PMID:1006"}
    assert found["HP:0000786"].absent and found["HP:0000786"].frequency == Frequency(0.0, "0/4")
    assert not found["HP:0001250"].absent


@pytest.mark.parametrize(
    ("finding", "feature", "relation"),
    [
        ("HP:0000407", "HP:0000407", "same"),
        ("HP:0008619", "HP:0000407", "more specific"),  # bilateral SNHL is a kind of SNHL
        ("HP:0008619", "HP:0000365", "more specific"),  # ...and of hearing impairment
        ("HP:0000365", "HP:0000407", "less specific"),
        ("HP:0000407", "HP:0001250", None),
    ],
)
def test_how_a_finding_stands_to_a_feature(
    hpo: HPO, finding: str, feature: str, relation: str | None
) -> None:
    assert hpo.relation(finding, feature) == relation

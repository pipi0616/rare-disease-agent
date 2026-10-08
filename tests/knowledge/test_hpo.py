"""The HPO release in memory, on a miniature of the real files (tests/fixtures/hpo)."""

import shutil
from pathlib import Path
from typing import Any

import pytest

from raredx.knowledge import hpo as hpo_module
from raredx.knowledge.hpo import HPO

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "hpo"


def terms(hpo_set: Any) -> set[str]:
    return {term.id for term in hpo_set}


def profiles(hpo: HPO, masked: frozenset[str] = frozenset()) -> dict[str, set[str]]:
    return {d: terms(p) for d, p in zip(hpo.disease_ids, hpo.profiles(masked), strict=True)}


def test_the_release_is_the_one_hp_obo_declares(hpo: HPO) -> None:
    assert hpo.release == hpo_module.release_of(FIXTURE) == "2099-01-01"


def test_a_profile_holds_an_omim_diseases_phenotype_and_nothing_else(hpo: HPO) -> None:
    assert hpo.disease_ids == ["OMIM:690001", "OMIM:690002", "OMIM:690003", "OMIM:690004"]
    found = profiles(hpo)
    assert found["OMIM:690001"] == {"HP:0000407", "HP:0000786"}  # not its inheritance
    assert found["OMIM:690002"] == {"HP:0000407", "HP:0000510"}  # not the NOT line


def test_a_sign_looked_for_and_never_found_is_not_in_the_profile(hpo: HPO) -> None:
    # OMIM:690003 lists hearing impairment at 0/4: absent in all four patients.
    assert profiles(hpo)["OMIM:690003"] == {"HP:0001250"}


def test_genes_are_the_mendelian_ones(hpo: HPO) -> None:
    assert hpo.genes == {"OMIM:690001": ("GENEA",), "OMIM:690002": ("GENEB1", "GENEB2")}


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

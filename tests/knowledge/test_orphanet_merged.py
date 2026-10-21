"""The release with Orphanet's annotations merged in by disease identity (chapter 31)."""

from pathlib import Path

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.find_disease import FindDisease, resolve
from raredx.tools.rank_diseases import RankDiseases

SEIZURE, ROD_CONE, AMENORRHEA = "HP:0001250", "HP:0000510", "HP:0000786"


def test_an_orphanet_entry_equal_to_an_omim_disease_is_merged_into_it(knowledge: HPO) -> None:
    assert "ORPHA:9004" not in knowledge.names and knowledge.aliases["ORPHA:9004"] == "OMIM:690004"
    features = {f.term: f for f in knowledge.features("OMIM:690004")}
    assert set(features) == {AMENORRHEA, SEIZURE}  # Orphanet adds seizures
    assert features[AMENORRHEA].sources == {"PMID:1004", "ORPHA:9004"}
    assert knowledge.names["OMIM:690004"] == "Amenorrhea known from one paper"  # OMIM's name


def test_an_orphanet_entry_with_no_omim_disease_is_one_of_its_own(knowledge: HPO) -> None:
    assert knowledge.names["ORPHA:9002"] == "An Orphanet-only syndrome"
    assert {f.term for f in knowledge.features("ORPHA:9002")} == {SEIZURE, ROD_CONE}
    assert "ORPHA:9002" in knowledge.disease_ids


def test_without_identity_orphanet_is_not_read(hpo: HPO) -> None:
    assert not any(d.startswith("ORPHA:") for d in hpo.names) and not hpo.aliases


def test_every_id_finds_the_disease_it_names_here(knowledge: HPO) -> None:
    assert knowledge.canonical("OMIM:690001") == "OMIM:690001"
    assert knowledge.canonical("ORPHA:9001") == "OMIM:690001"  # merged
    assert knowledge.canonical("OMIM:699998") == "ORPHA:9002"  # equal by Mondo, not annotated
    assert knowledge.canonical("OMIM:999999") is None


def test_a_disease_known_only_from_the_masked_paper_is_hidden_with_orphanets_lines(
    knowledge: HPO, tmp_path: Path
) -> None:
    # OMIM:690004 is known from PMID:1004 alone; Orphanet's entry cites no paper, but its
    # description of such a disease likely rests on the same one: hidden whole.
    assert "OMIM:690004" in knowledge.known_only_from(frozenset({"PMID:1004"}))
    target = tmp_path / "phenotype.hpoa"
    knowledge.write_annotations(target, frozenset({"PMID:1004"}))
    written = {line.split("\t")[0] for line in target.read_text().splitlines()}
    assert "OMIM:690004" not in written and "ORPHA:9004" not in written
    assert "ORPHA:9002" in written


def test_the_ranking_and_checks_name_orphanet_diseases(knowledge: HPO) -> None:
    ranking = RankDiseases(knowledge)([SEIZURE, ROD_CONE])
    assert ranking.matches[0].disease_id == "ORPHA:9002"
    report = CheckMatch(knowledge)([AMENORRHEA], "ORPHA:9004")  # an alias: its OMIM disease
    assert report.disease_id == "OMIM:690004"
    with masking.masked(["PMID:1004"]):
        assert "OMIM:690004" not in [
            m.disease_id for m in RankDiseases(knowledge)([AMENORRHEA]).matches
        ]


def test_a_guessed_orphanet_code_resolves_to_the_disease_it_names(knowledge: HPO) -> None:
    find = FindDisease(knowledge)
    assert resolve("ORPHA:9001", "", find) == "OMIM:690001"
    assert resolve("Orphanet:9002", "", find) == "ORPHA:9002"
    assert resolve(None, "An Orphanet-only syndrome", find) == "ORPHA:9002"  # by name

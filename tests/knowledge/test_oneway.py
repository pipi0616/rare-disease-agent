"""One-directional Resnik similarity, against hpo3's own term similarity."""

import statistics

import pytest
from pyhpo import Ontology

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.knowledge.oneway import OneWayResnik
from raredx.tools.rank_diseases import RankDiseases

SNHL, AMENORRHEA, SEIZURE = "HP:0000407", "HP:0000786", "HP:0001250"


def by_hand(hpo: HPO, patient: list[str], disease: str) -> float:
    """The mean over the patient's findings of the best Resnik match among the disease's
    observed features, from hpo3's own term-to-term similarity."""
    features = [Ontology.get_hpo_object(f.term) for f in hpo.features(disease) if not f.absent]
    best = []
    for finding in hpo.patient(patient)[0]:
        best.append(
            max(
                (finding.similarity_score(f, kind="omim", method="resnik") for f in features),
                default=0.0,
            )
        )
    return statistics.mean(best)


@pytest.mark.parametrize("patient", [[SNHL, AMENORRHEA], [SEIZURE], [SNHL, SEIZURE, AMENORRHEA]])
def test_it_equals_the_mean_of_each_findings_best_resnik_match(
    hpo: HPO, patient: list[str]
) -> None:
    scores = OneWayResnik(hpo).scores(hpo.patient(patient)[0])
    for i, disease in enumerate(hpo.disease_ids):
        assert scores[i] == pytest.approx(by_hand(hpo, patient, disease))


def test_features_the_patient_lacks_do_not_count_against_a_disease(hpo: HPO) -> None:
    # OMIM:690005 has hearing loss and more; the patient only hearing loss.
    one_way = OneWayResnik(hpo).scores(hpo.patient([SNHL])[0])
    both = hpo.patient([SNHL])[0].similarity_scores(
        hpo.profiles(), kind="omim", method="resnik", combine="funSimAvg"
    )
    i = hpo.index("OMIM:690005")
    assert one_way[i] > both[i]


def test_a_disease_known_only_from_the_masked_paper_scores_nothing(hpo: HPO) -> None:
    oneway = OneWayResnik(hpo)
    patient = hpo.patient([AMENORRHEA])[0]
    i = hpo.index("OMIM:690004")
    assert oneway.scores(patient)[i] > 0
    assert oneway.scores(patient, frozenset({"PMID:1004"}))[i] == 0


def test_the_ranking_tool_offers_it(hpo: HPO) -> None:
    rank = RankDiseases(hpo, "resnik", "oneway")
    assert rank([SNHL, AMENORRHEA]).matches[0].disease_id == "OMIM:690001"
    with masking.masked(["PMID:1004"]):
        assert "OMIM:690004" not in [m.disease_id for m in rank([AMENORRHEA]).matches]
    with pytest.raises(ValueError, match="resnik"):
        RankDiseases(hpo, "lin", "oneway")

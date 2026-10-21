"""The candidate pool and its rows, on the miniature HPO release and patient bank."""

from collections.abc import Callable

import pytest

from raredx.baselines.similar_patients import SimilarPatientsRank
from raredx.data.cases import Case
from raredx.evals.systems import Candidate
from raredx.knowledge.hpo import HPO
from raredx.knowledge.prevalence import Band
from raredx.ranking.pool import FEATURES, Pool, Row
from raredx.tools.check_match import CheckMatch
from raredx.tools.find_similar_patients import FindSimilarPatients
from raredx.tools.rank_diseases import RankDiseases

SNHL, AMENORRHEA = "HP:0000407", "HP:0000786"


@pytest.fixture
def pool(hpo: HPO, patients: list[Case]) -> Pool:
    nearest = SimilarPatientsRank(FindSimilarPatients(hpo, patients, "test bank"))
    bands: dict[str, Band] = {"OMIM:690001": "1 in 100,000 or more"}
    return Pool(RankDiseases(hpo), CheckMatch(hpo), nearest, bands)


def by_disease(rows: list[Row]) -> dict[str, Row]:
    return {r.disease_id: r for r in rows}


def test_each_route_names_its_candidates_and_the_right_one_is_marked(
    pool: Pool, make_case: Callable[..., Case]
) -> None:
    case = make_case("c1", hpo_ids=[SNHL, AMENORRHEA], disease_id="OMIM:690001", pmid=None)
    guesses = [  # the model's answer: an id HPO knows, then a name without an id
        Candidate(disease_name="Seizure disorder", disease_id="OMIM:690003"),
        Candidate(disease_name="Hearing-ovarian syndrome"),
    ]
    rows = by_disease(pool.rows("dev", case, guesses))
    right = rows["OMIM:690001"]
    assert right.correct and not rows["OMIM:690003"].correct
    assert set(right.features) == set(FEATURES)
    assert (right.features["model"], right.features["phenotype"], right.features["patients"]) == (
        0.5,
        1.0,
        1.0,
    )
    assert right.features["routes"] == 3 and right.features["explained"] == 1.0
    assert right.features["common"] == 1.0 and rows["OMIM:690003"].features["common"] == 0.0
    assert rows["OMIM:690003"].features["model"] == 1.0


def test_a_published_patients_disease_hpo_does_not_annotate_is_not_a_candidate(
    pool: Pool, make_case: Callable[..., Case]
) -> None:
    case = make_case("c2", hpo_ids=[SNHL, AMENORRHEA], disease_id="OMIM:690001", pmid=None)
    assert "OMIM:699999" not in by_disease(pool.rows("dev", case, []))


def test_the_cases_own_paper_is_masked(pool: Pool, make_case: Callable[..., Case]) -> None:
    # OMIM:690004 is known only from PMID:1004: for that paper's case it does not exist,
    # whichever route would name it.
    guess = [Candidate(disease_name="Amenorrhea known from one paper", disease_id="OMIM:690004")]
    case = make_case("c3", hpo_ids=[AMENORRHEA], disease_id="OMIM:690004", pmid="PMID:1004")
    assert "OMIM:690004" not in by_disease(pool.rows("dev", case, guess))
    other = make_case("c4", hpo_ids=[AMENORRHEA], disease_id="OMIM:690004", pmid="PMID:9999")
    assert by_disease(pool.rows("dev", other, guess))["OMIM:690004"].correct


def test_an_extra_list_becomes_a_feature(pool: Pool, make_case: Callable[..., Case]) -> None:
    case = make_case("c5", hpo_ids=[SNHL, AMENORRHEA], disease_id="OMIM:690001", pmid=None)
    rows = by_disease(pool.rows("dev", case, [], {"v1.1": ["OMIM:690002", "OMIM:690001"]}))
    assert rows["OMIM:690001"].features["v1.1"] == 0.5
    assert rows["OMIM:690002"].features["v1.1"] == 1.0

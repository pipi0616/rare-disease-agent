"""The scoring rules, one test each."""

from collections.abc import Callable

import pytest

from raredx.data.cases import Case
from raredx.evals import scoring
from raredx.evals.systems import Candidate

PERRAULT_1 = Candidate(disease_name="Perrault syndrome 1", disease_id="OMIM:233400", gene="HSD17B4")
PERRAULT_7 = Candidate(disease_name="Perrault syndrome 7", disease_id="OMIM:621101", gene="DAP3")


@pytest.mark.parametrize(
    "raw", ["OMIM:621101", "MIM:621101", "OMIM 621101", "621101", " omim:621101 "]
)
def test_omim_numbers_are_recognised_however_written(raw: str) -> None:
    assert scoring.normalize_disease(raw) == "OMIM:621101"


@pytest.mark.parametrize("raw", [None, "", "Perrault syndrome", "OMIM:62110"])
def test_anything_else_is_not_a_disease_id(raw: str | None) -> None:
    assert scoring.normalize_disease(raw) is None


@pytest.mark.parametrize("raw", ["ORPHA:3464", "Orphanet:3464", "orpha 3464", " ORPHA_3464 "])
def test_an_orphanet_code_is_kept_as_one(raw: str) -> None:
    assert scoring.normalize_disease(raw) == "ORPHA:3464"


def test_rank_is_the_position_of_the_first_match(make_case: Callable[..., Case]) -> None:
    s = scoring.score_case(make_case("1"), [PERRAULT_1, PERRAULT_7])
    assert (s.disease_rank, s.gene_rank) == (2, 2)


def test_a_disease_name_without_its_number_does_not_count(make_case: Callable[..., Case]) -> None:
    s = scoring.score_case(make_case("1"), [Candidate(disease_name="Perrault syndrome 7")])
    assert s.disease_rank is None


def test_gene_matches_ignore_case_and_whitespace(make_case: Callable[..., Case]) -> None:
    s = scoring.score_case(
        make_case("1", gene="C10orf71"), [Candidate(disease_name="x", gene=" c10ORF71")]
    )
    assert s.gene_rank == 1


def test_no_answer_is_a_miss_that_stays_in_the_denominator(make_case: Callable[..., Case]) -> None:
    scores = [
        scoring.score_case(make_case("1"), [PERRAULT_7]),
        scoring.score_case(make_case("2"), []),
    ]
    summary = scoring.summarize(scores)
    assert (summary.n_cases, summary.n_answered) == (2, 1)
    assert summary.disease[1].hits == 1 and summary.disease[1].n == 2


def test_cases_without_a_gene_are_left_out_of_gene_numbers(make_case: Callable[..., Case]) -> None:
    scores = [
        scoring.score_case(make_case("1"), [PERRAULT_7]),
        scoring.score_case(make_case("2", gene=None), [PERRAULT_7]),
    ]
    summary = scoring.summarize(scores)
    assert summary.disease[1].n == 2
    assert summary.gene[1].n == 1


def test_top_k_counts_everything_ranked_k_or_better(make_case: Callable[..., Case]) -> None:
    answer = [PERRAULT_1, PERRAULT_1, PERRAULT_7]
    summary = scoring.summarize([scoring.score_case(make_case("1"), answer)])
    assert [summary.disease[k].hits for k in scoring.KS] == [0, 1, 1, 1]


def test_wilson_interval_matches_known_values() -> None:
    low, high = scoring.wilson(100, 200)
    assert (round(low, 3), round(high, 3)) == (0.431, 0.569)
    low, high = scoring.wilson(0, 200)
    assert low == 0.0 and round(high, 3) == 0.019


def test_the_sign_test_counts_only_the_cases_the_systems_disagree_on() -> None:
    assert scoring.sign_test(11, 1) == pytest.approx(0.00635, abs=1e-5)
    assert scoring.sign_test(1, 11) == scoring.sign_test(11, 1)  # either order
    assert scoring.sign_test(5, 5) == 1.0  # an even split is no evidence either way
    assert scoring.sign_test(0, 0) == 1.0  # no disagreement, nothing to test


def test_a_tiny_p_value_is_not_printed_as_zero() -> None:
    assert scoring.p_value(4.04e-09) == "p < 0.001"
    assert scoring.p_value(0.0131) == "p = 0.013"
    assert scoring.p_value(1.0) == "p = 1.000"


def test_with_disease_identity_an_equal_id_is_found_too() -> None:
    answer = [Candidate(disease_name="Behçet disease", disease_id="ORPHA:117")]

    def same(disease: str) -> set[str]:
        return (
            {"OMIM:109650", "ORPHA:117"} if disease in ("OMIM:109650", "ORPHA:117") else {disease}
        )

    assert scoring.ranks(answer, "OMIM:109650", None) == (None, None)  # by the ids as written
    assert scoring.ranks(answer, "OMIM:109650", None, [], same) == (1, None)
    assert scoring.accepted_ids("OMIM:109650", ["OMIM:999999"], same) == {
        "OMIM:109650",
        "ORPHA:117",
        "OMIM:999999",
    }

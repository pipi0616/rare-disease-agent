"""Rank, then check: the two-stage baseline, on the miniature HPO release."""

from collections.abc import Callable

from raredx.baselines.phenotype_rank import PhenotypeRank
from raredx.baselines.rank_then_check import RankThenCheck
from raredx.data.cases import Case
from raredx.evals.systems import question_of
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.rank_diseases import RankDiseases


def answers(system: PhenotypeRank | RankThenCheck, case: Case) -> list[str]:
    return [c.disease_id or "" for c in system.predict(question_of(case))]


def test_the_disease_explaining_more_findings_moves_up(
    hpo: HPO, make_case: Callable[..., Case]
) -> None:
    # Hearing loss and seizures: similarity prefers the seizure-only disease, whose short
    # list matches perfectly; OMIM:690005 explains both findings.
    case = make_case("1", hpo_ids=["HP:0000407", "HP:0001250"], hpo_labels=["a", "b"])
    rank = RankDiseases(hpo)
    assert answers(PhenotypeRank(rank), case)[:2] == ["OMIM:690003", "OMIM:690005"]
    assert answers(RankThenCheck(rank, CheckMatch(hpo)), case)[:2] == [
        "OMIM:690005",
        "OMIM:690003",
    ]


def test_diseases_explaining_as_much_keep_the_similarity_order(
    hpo: HPO, make_case: Callable[..., Case]
) -> None:
    case = make_case(
        "1", hpo_ids=["HP:0000407", "HP:0000786", "HP:0001250"], hpo_labels=["a", "b", "c"]
    )
    rank = RankDiseases(hpo)
    similarity = answers(PhenotypeRank(rank), case)
    checked = answers(RankThenCheck(rank, CheckMatch(hpo)), case)
    # 690005 and 690001 each explain two findings; 690005 came first by similarity.
    assert similarity.index("OMIM:690005") < similarity.index("OMIM:690001")
    assert checked[:2] == ["OMIM:690005", "OMIM:690001"]


def test_a_run_records_the_pool_and_the_ordering_rule(hpo: HPO) -> None:
    system = RankThenCheck(RankDiseases(hpo), CheckMatch(hpo))
    assert system.name == "rank-then-check"
    assert system.params() == {
        "hpo_release": "2099-01-01",
        "similarity": "resnik/funSimAvg",
        "pool": "30",
        "order": "findings explained, then similarity",
    }

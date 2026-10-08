"""The boundary systems work behind, and the two reference systems."""

from collections.abc import Callable

from raredx.data.cases import Case
from raredx.evals.systems import Oracle, Popularity, Question, question_of


def test_a_question_carries_no_part_of_the_answer(make_case: Callable[..., Case]) -> None:
    allowed = {"case_id", "hpo_ids", "hpo_labels", "sex"}
    assert set(Question.model_fields) == allowed
    q = question_of(make_case("1")).model_dump_json()
    assert "OMIM" not in q and "DAP3" not in q and "PMID" not in q and "Perrault" not in q


def test_oracle_answers_with_the_confirmed_diagnosis(make_case: Callable[..., Case]) -> None:
    case = make_case("1")
    [answer] = Oracle.from_cases([case]).predict(question_of(case))
    assert (answer.disease_id, answer.gene) == (case.disease_id, case.gene)


def test_popularity_ranks_diseases_by_papers_not_by_patients(
    make_case: Callable[..., Case],
) -> None:
    big_report = [make_case(f"big{i}", disease_id="OMIM:100001", pmid="PMID:1") for i in range(50)]
    two_papers = [
        make_case(f"p{i}", disease_id="OMIM:100002", pmid=f"PMID:{10 + i}") for i in range(2)
    ]
    ranked = Popularity.from_cases(big_report + two_papers, k=2).predict(question_of(two_papers[0]))
    assert [c.disease_id for c in ranked] == ["OMIM:100002", "OMIM:100001"]


def test_popularity_gives_every_patient_the_same_answer(make_case: Callable[..., Case]) -> None:
    pool = [make_case(str(i), disease_id=f"OMIM:1000{i:02d}") for i in range(20)]
    system = Popularity.from_cases(pool)
    first, second = (system.predict(question_of(make_case(x))) for x in ("a", "b"))
    assert first == second and len(first) == 10

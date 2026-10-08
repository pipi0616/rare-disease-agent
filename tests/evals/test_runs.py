"""Running and scoring: failures recorded, answers scored against one manifest."""

from collections.abc import Callable

import pytest

from raredx.data.cases import Case
from raredx.evals import runs
from raredx.evals.systems import Candidate, Oracle, Question


@pytest.fixture
def cases(make_case: Callable[..., Case]) -> list[Case]:
    return [make_case(str(i)) for i in range(5)]


class Flaky:
    name = "flaky"

    def predict(self, question: Question) -> list[Candidate]:
        if question.case_id == "3":
            raise TimeoutError("model did not answer")
        return [Candidate(disease_name="Perrault syndrome 7", disease_id="621101")]


def test_a_failure_is_recorded_and_scored_as_a_miss(cases: list[Case]) -> None:
    records = runs.execute(Flaky(), cases)
    assert [r.error for r in records if r.error] == ["TimeoutError: model did not answer"]
    summary, _ = runs.score(records, [c.id for c in cases], {c.id: c for c in cases})
    assert (summary.n_cases, summary.n_answered, summary.disease[1].hits) == (5, 4, 4)


def test_a_case_with_no_record_at_all_still_counts(cases: list[Case]) -> None:
    records = runs.execute(Oracle.from_cases(cases), cases[:3])
    summary, _ = runs.score(records, [c.id for c in cases], {c.id: c for c in cases})
    assert (summary.n_cases, summary.disease[1].hits) == (5, 3)


def test_answers_for_cases_outside_the_manifest_are_refused(cases: list[Case]) -> None:
    records = runs.execute(Oracle.from_cases(cases), cases)
    with pytest.raises(ValueError, match="outside the manifest"):
        runs.score(records, [c.id for c in cases[:2]], {c.id: c for c in cases})

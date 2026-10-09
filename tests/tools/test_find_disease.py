"""find_disease, on the miniature HPO release's five disease names."""

import mlflow
import pytest
from pydantic import ValidationError

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.find_disease import FindDisease


@pytest.fixture
def find(hpo: HPO) -> FindDisease:
    return FindDisease(hpo)


def test_an_exact_name_comes_first_at_full_similarity(find: FindDisease) -> None:
    [first, *_] = find("Seizure disorder").matches
    assert (first.disease_id, first.disease_name, first.similarity) == (
        "OMIM:690003",
        "Seizure disorder",
        100,
    )


def test_a_loosely_written_name_still_finds_the_disease(find: FindDisease) -> None:
    # Different case, no hyphen, words only partly given.
    assert find("hearing ovarian").matches[0].disease_id == "OMIM:690001"
    assert find("frequency test").matches[0].disease_id == "OMIM:690005"


def test_limit_caps_the_list(find: FindDisease) -> None:
    assert len(find("syndrome", limit=2).matches) == 2
    assert len(find("syndrome").matches) == 5  # the default; the fixture has five diseases


def test_a_name_too_short_to_search_is_refused(find: FindDisease) -> None:
    with pytest.raises(ValidationError):
        find("ab")


def test_each_search_is_recorded_as_a_tool_span(find: FindDisease) -> None:
    find("Seizure disorder")
    mlflow.flush_trace_async_logging()
    trace_id = mlflow.get_last_active_trace_id()
    assert trace_id is not None
    trace = mlflow.get_trace(trace_id)
    assert trace is not None
    [span] = trace.data.spans
    assert (span.name, span.span_type) == ("find_disease", "TOOL")


def test_a_disease_known_only_from_a_masked_paper_is_not_found_by_name(
    find: FindDisease,
) -> None:
    name = "Amenorrhea known from one paper"
    assert find(name).matches[0].disease_id == "OMIM:690004"
    with masking.masked(["PMID:1004"]):
        assert "OMIM:690004" not in [m.disease_id for m in find(name).matches]
    with masking.masked(["PMID:1001"]):  # another paper: it is still there
        assert find(name).matches[0].disease_id == "OMIM:690004"

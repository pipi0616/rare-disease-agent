"""T5, find similar patients, on a small bank over the miniature HPO release."""

from collections.abc import Callable

import mlflow
import pytest
from pydantic import ValidationError

from raredx.data.cases import Case
from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.find_similar_patients import FindSimilarPatients

SNHL, BILATERAL, AMENORRHEA = "HP:0000407", "HP:0008619", "HP:0000786"
ROD_CONE, SEIZURE = "HP:0000510", "HP:0001250"


@pytest.fixture
def find(hpo: HPO, patients: list[Case]) -> FindSimilarPatients:
    return FindSimilarPatients(hpo, patients, "test bank")


def test_the_most_similar_patients_come_first_with_their_diagnoses(
    find: FindSimilarPatients,
) -> None:
    result = find([SNHL, AMENORRHEA])
    first = result.patients[0]
    assert (first.disease_id, first.disease_name, first.source) == (
        "OMIM:690001",
        "Hearing-ovarian syndrome",
        "PMID:2001",
    )
    assert first.shared == ["Sensorineural hearing impairment", "Primary amenorrhea"]
    scores = [p.similarity for p in result.patients]
    assert scores == sorted(scores, reverse=True)
    assert result.searched == 5


def test_a_finding_more_specific_than_the_other_patients_still_counts_as_shared(
    find: FindSimilarPatients,
) -> None:
    [retina] = [p for p in find([BILATERAL, ROD_CONE]).patients if p.source == "PMID:2003"]
    assert retina.shared == [  # in term order
        "Rod-cone dystrophy",
        "Bilateral sensorineural hearing impairment",
    ]


def test_it_finds_a_disease_the_hpo_annotations_do_not_have(find: FindSimilarPatients) -> None:
    diseases = [p.disease_id for p in find([SNHL, AMENORRHEA, SEIZURE]).patients]
    assert diseases[0] == "OMIM:699999"


def test_patients_from_a_masked_paper_are_not_found(find: FindSimilarPatients) -> None:
    with masking.masked(["PMID:2001"]):
        result = find([SNHL, AMENORRHEA])
    assert "PMID:2001" not in [p.source for p in result.patients]
    assert result.searched == 4


def test_top_k_caps_the_list_and_has_a_limit(find: FindSimilarPatients) -> None:
    assert len(find([SNHL, AMENORRHEA], top_k=2).patients) == 2
    with pytest.raises(ValidationError):
        find([SNHL], top_k=51)


def test_unknown_terms_are_reported_and_left_out(find: FindSimilarPatients) -> None:
    result = find([SNHL, "HP:9999999"])
    assert result.unrecognized == ["HP:9999999"]
    assert result.patients


def test_each_search_is_recorded_as_a_tool_span(find: FindSimilarPatients) -> None:
    find([SNHL])
    mlflow.flush_trace_async_logging()
    trace_id = mlflow.get_last_active_trace_id()
    assert trace_id is not None
    trace = mlflow.get_trace(trace_id)
    assert trace is not None
    [span] = trace.data.spans
    assert (span.name, span.span_type) == ("find_similar_patients", "TOOL")


def test_patients_of_a_disease_known_only_from_a_masked_paper_are_not_found(
    hpo: HPO, patients: list[Case], make_case: Callable[..., Case]
) -> None:
    # A patient of OMIM:690004 from another paper; HPO knows the disease from PMID:1004 alone.
    other = make_case(
        "p9", hpo_ids=[AMENORRHEA], hpo_labels=["a"], disease_id="OMIM:690004", pmid="PMID:2009"
    )
    find = FindSimilarPatients(hpo, [*patients, other], "test bank")
    assert "PMID:2009" in [p.source for p in find([AMENORRHEA]).patients]
    with masking.masked(["PMID:1004"]):
        result = find([AMENORRHEA])
    assert "OMIM:690004" not in [p.disease_id for p in result.patients]
    assert result.searched == 5

"""T4, check a match, on the miniature HPO release."""

import mlflow
import pytest
from pydantic import ValidationError

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch, MatchReport
from raredx.tools.ids import UnknownDisease

SNHL, BILATERAL, HEARING = "HP:0000407", "HP:0008619", "HP:0000365"
AMENORRHEA, SEIZURE, ROD_CONE = "HP:0000786", "HP:0001250", "HP:0000510"


@pytest.fixture
def check(hpo: HPO) -> CheckMatch:
    return CheckMatch(hpo)


def explained(report: MatchReport) -> list[tuple[str, str, str]]:
    return [(e.finding.hpo_id, e.feature, e.relation) for e in report.explained]


def test_findings_the_disease_shows_are_explained(check: CheckMatch) -> None:
    report = check([AMENORRHEA, SNHL], "OMIM:690001")
    assert explained(report) == [  # in term order
        (SNHL, "Sensorineural hearing impairment", "same"),
        (AMENORRHEA, "Primary amenorrhea", "same"),
    ]
    assert report.n_findings == 2
    assert report.unexplained == [] and report.contradicted == []
    assert report.explained[0].frequency == "2/2"
    assert report.explained[0].sources == ["PMID:1001"]


def test_a_finding_more_or_less_specific_than_a_feature_is_still_explained(
    check: CheckMatch,
) -> None:
    # Bilateral SNHL is a kind of SNHL; Hearing impairment is the broader term above it.
    assert explained(check([BILATERAL], "OMIM:690001")) == [
        (BILATERAL, "Sensorineural hearing impairment", "more specific")
    ]
    assert explained(check([HEARING], "OMIM:690001")) == [
        (HEARING, "Sensorineural hearing impairment", "less specific")
    ]


def test_a_finding_the_disease_does_not_show_is_unexplained(check: CheckMatch) -> None:
    report = check([SNHL, SEIZURE], "OMIM:690001")
    assert [f.hpo_id for f in report.unexplained] == [SEIZURE]


def test_a_finding_its_sources_looked_for_and_never_saw_is_a_contradiction(
    check: CheckMatch,
) -> None:
    # OMIM:690003 records hearing impairment at 0/4; SNHL is a kind of hearing impairment.
    report = check([SNHL], "OMIM:690003")
    [c] = report.contradicted
    assert (c.finding.hpo_id, c.feature, c.frequency) == (SNHL, "Hearing impairment", "0/4")
    assert c.sources == ["PMID:1003"] and report.unexplained == []


def test_frequent_features_the_patient_lacks_are_missing(check: CheckMatch) -> None:
    # OMIM:690005: rod-cone dystrophy is frequent (about 55%), SNHL 4/8; seizure, frequency unknown.
    report = check([SEIZURE], "OMIM:690005")
    assert [(m.feature.hpo_id, m.frequency) for m in report.missing] == [
        (ROD_CONE, "frequent (30–79%)"),
        (SNHL, "4/8"),
    ]
    assert report.n_missing == 2
    assert [m.feature.hpo_id for m in check([SNHL], "OMIM:690005").missing] == [ROD_CONE]


def test_masked_sources_drop_out_of_the_comparison(check: CheckMatch) -> None:
    with masking.masked(["PMID:1005"]):
        report = check([SEIZURE], "OMIM:690005")
    # Only SNHL at 1/4 is left: seizure is unexplained, and nothing is frequent enough to miss.
    assert [f.hpo_id for f in report.unexplained] == [SEIZURE]
    assert report.missing == [] and report.n_missing == 0
    assert "mask" not in report.model_dump_json().lower()


def test_unknown_terms_are_reported_and_left_out(check: CheckMatch) -> None:
    report = check([SNHL, "HP:0123456"], "OMIM:690001")
    assert report.unrecognized == ["HP:0123456"] and report.n_findings == 1


def test_an_unknown_disease_is_an_error_the_model_can_act_on(check: CheckMatch) -> None:
    with pytest.raises(UnknownDisease, match="rank_diseases"):
        check([SNHL], "OMIM:999999")


@pytest.mark.parametrize(
    ("hpo_ids", "disease_id"), [([], "OMIM:690001"), ([SNHL], "690001"), (["deaf"], "OMIM:690001")]
)
def test_malformed_input_is_refused(check: CheckMatch, hpo_ids: list[str], disease_id: str) -> None:
    with pytest.raises(ValidationError):
        check(hpo_ids, disease_id)


def test_each_check_is_recorded_as_a_tool_span(check: CheckMatch) -> None:
    check([SNHL], "OMIM:690001")
    mlflow.flush_trace_async_logging()
    trace_id = mlflow.get_last_active_trace_id()
    assert trace_id is not None
    trace = mlflow.get_trace(trace_id)
    assert trace is not None
    [span] = trace.data.spans
    assert (span.name, span.span_type) == ("check_match", "TOOL")
    assert span.inputs == {"hpo_ids": [SNHL], "disease_id": "OMIM:690001"}

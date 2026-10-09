"""T3, look up a disease, on the miniature HPO release."""

import mlflow
import pytest
from pydantic import ValidationError

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.ids import UnknownDisease
from raredx.tools.lookup_disease import DiseaseProfile, LookupDisease


@pytest.fixture
def lookup(hpo: HPO) -> LookupDisease:
    return LookupDisease(hpo)


def features(profile: DiseaseProfile) -> list[tuple[str, str | None]]:
    return [(f.hpo_id, f.frequency) for f in profile.features]


def test_a_profile_says_what_hpo_records_most_frequent_first(lookup: LookupDisease) -> None:
    profile = lookup("OMIM:690005")
    # frequent (about 55%) before 4 of 8; unknown frequency last; the 0/4 sign is no feature
    assert features(profile) == [
        ("HP:0000510", "frequent (30–79%)"),
        ("HP:0000407", "4/8"),
        ("HP:0001250", None),
    ]
    assert profile.n_features == 3
    assert profile.inheritance == ["Autosomal recessive inheritance"]
    assert profile.onset_and_course == ["Congenital onset"]
    assert profile.genes == ["GENEE"]
    assert profile.sources == ["PMID:1005", "PMID:1006"]
    assert profile.features[1].sources == ["PMID:1005", "PMID:1006"]


def test_max_features_cuts_the_list_and_the_total_says_so(lookup: LookupDisease) -> None:
    profile = lookup("OMIM:690005", max_features=1)
    assert len(profile.features) == 1 and profile.n_features == 3


def test_masked_sources_drop_out_of_every_part_of_the_answer(lookup: LookupDisease) -> None:
    with masking.masked(["PMID:1006"]):
        assert features(lookup("OMIM:690005"))[0] == ("HP:0000407", "3/4")
    with masking.masked(["PMID:1005"]):
        profile = lookup("OMIM:690005")
    assert features(profile) == [("HP:0000407", "1/4")]
    assert (profile.inheritance, profile.onset_and_course) == ([], [])
    assert profile.sources == ["PMID:1006"]


def test_a_disease_known_only_from_a_masked_paper_does_not_exist(lookup: LookupDisease) -> None:
    with masking.masked(["PMID:1004"]), pytest.raises(UnknownDisease) as hidden:
        lookup("OMIM:690004")
    with pytest.raises(UnknownDisease) as unknown:
        lookup("OMIM:999999")
    # The same words as for any unknown id: the model is never told something was hidden.
    assert str(hidden.value) == str(unknown.value).replace("999999", "690004")


def test_a_kept_feature_does_not_list_the_masked_paper_among_its_sources(
    lookup: LookupDisease,
) -> None:
    # OMIM:690002's rod-cone dystrophy cites PMID:1002 and its OMIM entry.
    with masking.masked(["PMID:1002"]):
        profile = lookup("OMIM:690002")
    assert features(profile) == [("HP:0000510", None)]
    assert profile.features[0].sources == ["OMIM:690002"] and profile.sources == ["OMIM:690002"]


def test_an_unknown_disease_is_an_error_the_model_can_act_on(lookup: LookupDisease) -> None:
    with pytest.raises(UnknownDisease, match="rank_diseases"):
        lookup("OMIM:999999")


@pytest.mark.parametrize("disease_id", ["690001", "OMIM:12", "ORPHA:9001"])
def test_a_malformed_id_is_refused(lookup: LookupDisease, disease_id: str) -> None:
    with pytest.raises(ValidationError):
        lookup(disease_id)


def test_each_lookup_is_recorded_as_a_tool_span(lookup: LookupDisease) -> None:
    lookup("OMIM:690001")
    mlflow.flush_trace_async_logging()
    trace_id = mlflow.get_last_active_trace_id()
    assert trace_id is not None
    trace = mlflow.get_trace(trace_id)
    assert trace is not None
    [span] = trace.data.spans
    assert (span.name, span.span_type) == ("lookup_disease", "TOOL")
    assert span.inputs == {"disease_id": "OMIM:690001", "max_features": 20}

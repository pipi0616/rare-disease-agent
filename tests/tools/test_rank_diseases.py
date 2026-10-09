"""T2, rank diseases by phenotype, on the miniature HPO release."""

import mlflow
import pytest
from pydantic import ValidationError

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.rank_diseases import RankDiseases, Ranking


@pytest.fixture
def rank(hpo: HPO) -> RankDiseases:
    return RankDiseases(hpo)


def ids(ranking: Ranking) -> list[str]:
    return [m.disease_id for m in ranking.matches]


def test_the_disease_showing_all_the_patients_signs_ranks_first(rank: RankDiseases) -> None:
    ranking = rank(["HP:0000407", "HP:0000786"])
    assert ids(ranking)[0] == "OMIM:690001"
    assert ranking.matches[0].genes == ["GENEA"] and ranking.hpo_release == "2099-01-01"


def test_a_disease_known_only_from_the_masked_paper_disappears(rank: RankDiseases) -> None:
    assert ids(rank(["HP:0000786"]))[0] == "OMIM:690004"
    with masking.masked(["PMID:1004"]):
        assert "OMIM:690004" not in ids(rank(["HP:0000786"]))


def test_a_sign_recorded_as_absent_does_not_match(rank: RankDiseases) -> None:
    # OMIM:690003 lists hearing impairment at 0/4.
    assert "OMIM:690003" not in ids(rank(["HP:0000365"]))


def test_unknown_terms_are_reported_not_fatal(rank: RankDiseases) -> None:
    ranking = rank(["HP:0000407", "HP:0123456"])
    assert ranking.unrecognized == ["HP:0123456"] and ranking.matches
    assert rank(["HP:0123456"]).matches == []


def test_top_k_limits_the_list(rank: RankDiseases) -> None:
    assert len(rank(["HP:0000407"], top_k=1).matches) == 1


@pytest.mark.parametrize(
    ("hpo_ids", "top_k"),
    [([], 10), (["hearing loss"], 10), (["HP:0000407"], 0), (["HP:0000407"], 51)],
)
def test_malformed_input_is_refused(rank: RankDiseases, hpo_ids: list[str], top_k: int) -> None:
    with pytest.raises(ValidationError):
        rank(hpo_ids, top_k=top_k)


def test_an_unknown_similarity_is_refused(hpo: HPO) -> None:
    with pytest.raises(ValueError, match="unknown similarity"):
        RankDiseases(hpo, "cosine", "funSimAvg")


def test_each_call_is_recorded_as_a_tool_span(rank: RankDiseases) -> None:
    rank(["HP:0000407", "HP:0000786"])
    mlflow.flush_trace_async_logging()
    trace_id = mlflow.get_last_active_trace_id()
    assert trace_id is not None
    trace = mlflow.get_trace(trace_id)
    assert trace is not None
    [span] = trace.data.spans
    assert (span.name, span.span_type) == ("rank_diseases", "TOOL")
    assert span.inputs == {"hpo_ids": ["HP:0000407", "HP:0000786"], "top_k": 10}
    assert span.outputs["matches"][0]["disease_id"] == "OMIM:690001"


def test_a_disease_known_only_from_a_masked_paper_is_never_ranked(hpo: HPO) -> None:
    rank = RankDiseases(hpo)
    assert "OMIM:690004" in [m.disease_id for m in rank(["HP:0000786"], top_k=10).matches]
    with masking.masked(["PMID:1004"]):
        assert "OMIM:690004" not in [m.disease_id for m in rank(["HP:0000786"], top_k=10).matches]

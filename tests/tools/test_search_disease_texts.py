"""T6, search disease texts, over the miniature texts and HPO release."""

import mlflow
import pytest
from pydantic import ValidationError

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.knowledge.text_index import TextIndex
from raredx.knowledge.texts import Passage
from raredx.tools.search_disease_texts import SearchDiseaseTexts


@pytest.fixture
def search(text_index: TextIndex[Passage], hpo: HPO) -> SearchDiseaseTexts:
    return SearchDiseaseTexts(text_index, hpo)


def test_a_search_returns_passages_with_their_diseases_and_sources(
    search: SearchDiseaseTexts,
) -> None:
    result = search("ovarian failure with hearing loss", top_k=2)
    first = result.hits[0]
    assert (first.disease_ids, first.disease_name, first.source) == (
        ["OMIM:690001"],
        "Hearing-ovarian syndrome",
        "Orphanet ORPHA:9101",
    )
    assert "ovarian failure" in first.text
    assert len(result.hits) == 2 and result.searched == 4


def test_a_disease_known_only_from_a_masked_paper_is_hidden(search: SearchDiseaseTexts) -> None:
    # HPO knows OMIM:690004 from PMID:1004 alone: its description likely rests on that paper.
    with masking.masked(["PMID:1004"]):
        result = search("primary amenorrhea in a single family", top_k=5)
    assert all("OMIM:690004" not in h.disease_ids for h in result.hits)
    assert result.searched == 3


def test_a_disease_with_other_sources_stays_when_one_paper_is_masked(
    search: SearchDiseaseTexts,
) -> None:
    # OMIM:690002 also cites its OMIM entry, so masking PMID:1002 leaves it known.
    with masking.masked(["PMID:1002"]):
        result = search("night blindness", top_k=1)
    assert result.hits[0].disease_ids == ["OMIM:690002"]


def test_a_query_too_short_or_too_many_results_is_refused(search: SearchDiseaseTexts) -> None:
    with pytest.raises(ValidationError):
        search("ab")
    with pytest.raises(ValidationError):
        search("hearing loss", top_k=21)


def test_each_search_is_recorded_as_a_tool_span(search: SearchDiseaseTexts) -> None:
    search("hearing loss")
    mlflow.flush_trace_async_logging()
    trace_id = mlflow.get_last_active_trace_id()
    assert trace_id is not None
    trace = mlflow.get_trace(trace_id)
    assert trace is not None
    [span] = trace.data.spans
    assert (span.name, span.span_type) == ("search_disease_texts", "TOOL")

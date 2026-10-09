"""T7, rank candidate genes, on the miniature HPO release."""

import mlflow
import pytest
from pydantic import ValidationError

from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO
from raredx.tools.rank_candidate_genes import RankCandidateGenes

SNHL, AMENORRHEA = "HP:0000407", "HP:0000786"


@pytest.fixture
def rank(hpo: HPO) -> RankCandidateGenes:
    return RankCandidateGenes(hpo)


def test_the_gene_whose_disease_matches_best_comes_first(rank: RankCandidateGenes) -> None:
    ranking = rank([SNHL, AMENORRHEA], ["GENEB1", "GENEA", "GENEE"])
    assert [m.gene for m in ranking.genes][0] == "GENEA"
    first = ranking.genes[0]
    assert first.diseases[0].disease_id == "OMIM:690001" and first.n_diseases == 1
    scores = [m.best_score for m in ranking.genes]
    assert scores == sorted(scores, reverse=True)


def test_a_gene_with_no_known_disease_is_listed_apart(rank: RankCandidateGenes) -> None:
    ranking = rank([SNHL], ["GENEA", "NOVEL1", "GENEA"])  # a repeat counts once
    assert [m.gene for m in ranking.genes] == ["GENEA"]
    assert ranking.no_known_disease == ["NOVEL1"]


def test_a_disease_known_only_from_a_masked_paper_leaves_its_gene_unscored(
    rank: RankCandidateGenes,
) -> None:
    # HPO knows OMIM:690001, GENEA's disease, from PMID:1001 alone.
    with masking.masked(["PMID:1001"]):
        ranking = rank([SNHL, AMENORRHEA], ["GENEA", "GENEE"])
    assert "GENEA" in ranking.no_known_disease
    assert "OMIM:690001" not in ranking.model_dump_json()


def test_top_k_and_the_input_are_checked(rank: RankCandidateGenes) -> None:
    assert len(rank([SNHL], ["GENEA", "GENEB1", "GENEE"], top_k=1).genes) == 1
    with pytest.raises(ValidationError):
        rank([SNHL], ["not a gene!"])
    with pytest.raises(ValidationError):
        rank([SNHL], [])


def test_each_ranking_is_recorded_as_a_tool_span(rank: RankCandidateGenes) -> None:
    rank([SNHL], ["GENEA"])
    mlflow.flush_trace_async_logging()
    trace = mlflow.get_trace(mlflow.get_last_active_trace_id() or "")
    assert trace is not None
    [span] = trace.data.spans
    assert (span.name, span.span_type) == ("rank_candidate_genes", "TOOL")


def test_a_gene_whose_disease_has_no_phenotype_annotations_cannot_be_scored(
    rank: RankCandidateGenes,
) -> None:
    # GENEF causes OMIM:699998, which has no phenotype annotation in the release.
    assert rank([SNHL], ["GENEF", "GENEA"]).no_known_disease == ["GENEF"]

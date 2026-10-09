"""B0g, candidate genes ranked by phenotype, on the miniature HPO release."""

from collections.abc import Callable

import pytest

from raredx.baselines.gene_rank import GeneRank
from raredx.data.cases import Case
from raredx.evals.systems import question_of
from raredx.knowledge.hpo import HPO
from raredx.tools.rank_candidate_genes import RankCandidateGenes


def test_the_diseases_of_the_best_ranked_genes_come_first_with_their_genes(
    hpo: HPO, make_case: Callable[..., Case]
) -> None:
    case = make_case("1", hpo_ids=["HP:0000407", "HP:0000786"], hpo_labels=["a", "b"])
    question = question_of(case).model_copy(
        update={"candidate_genes": ["GENEA", "GENEB1", "GENEE"]}
    )
    answers = GeneRank(RankCandidateGenes(hpo)).predict(question)
    assert (answers[0].disease_id, answers[0].gene) == ("OMIM:690001", "GENEA")


def test_without_candidate_genes_it_refuses(hpo: HPO, make_case: Callable[..., Case]) -> None:
    with pytest.raises(ValueError, match="with-genes"):
        GeneRank(RankCandidateGenes(hpo)).predict(question_of(make_case("1")))

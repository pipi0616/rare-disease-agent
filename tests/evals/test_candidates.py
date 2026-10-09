"""The genotype track's simulated sequencing, on the miniature HPO release."""

from collections.abc import Callable

import pytest

from raredx.data.cases import Case
from raredx.evals.candidates import candidate_genes
from raredx.knowledge.hpo import HPO


def test_the_list_holds_the_causal_gene_and_decoys_sorted(
    hpo: HPO, make_case: Callable[..., Case]
) -> None:
    case = make_case("1", disease_id="OMIM:690002", gene="GENEB1")
    genes = candidate_genes(case, hpo, n=3)
    # GENEB2 also causes OMIM:690002, so it is never a decoy: only GENEA and GENEE are left.
    assert genes == ["GENEA", "GENEB1", "GENEE"]
    assert genes == sorted(genes)


def test_the_draw_is_the_same_every_time(hpo: HPO, make_case: Callable[..., Case]) -> None:
    case = make_case("7", disease_id="OMIM:690005", gene="GENEE")
    assert candidate_genes(case, hpo, n=2) == candidate_genes(case, hpo, n=2)


def test_a_case_without_a_causal_gene_has_nothing_to_sequence(
    hpo: HPO, make_case: Callable[..., Case]
) -> None:
    with pytest.raises(ValueError, match="no causal gene"):
        candidate_genes(make_case("1", gene=None), hpo, n=2)

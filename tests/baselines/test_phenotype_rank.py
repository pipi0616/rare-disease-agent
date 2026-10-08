"""B0, the phenotype-only baseline, on the miniature HPO release."""

from collections.abc import Callable

from raredx.baselines.phenotype_rank import PhenotypeRank
from raredx.data.cases import Case
from raredx.evals.systems import question_of
from raredx.knowledge.hpo import HPO
from raredx.tools.rank_diseases import RankDiseases


def test_the_tools_ranking_becomes_the_answer(hpo: HPO, make_case: Callable[..., Case]) -> None:
    case = make_case("1", hpo_ids=["HP:0000407", "HP:0000786"], hpo_labels=["a", "b"])
    [first, *_] = PhenotypeRank(RankDiseases(hpo)).predict(question_of(case))
    assert (first.disease_id, first.disease_name, first.gene) == (
        "OMIM:690001",
        "Hearing-ovarian syndrome",
        "GENEA",
    )


def test_a_disease_with_several_genes_names_none(hpo: HPO, make_case: Callable[..., Case]) -> None:
    case = make_case("1", hpo_ids=["HP:0000510"], hpo_labels=["Rod-cone dystrophy"])
    [first, *_] = PhenotypeRank(RankDiseases(hpo)).predict(question_of(case))
    assert first.disease_id == "OMIM:690002" and first.gene is None


def test_a_run_records_the_release_and_the_similarity(hpo: HPO) -> None:
    system = PhenotypeRank(RankDiseases(hpo))
    assert system.name == "phenotype-rank"
    assert system.params() == {"hpo_release": "2099-01-01", "similarity": "resnik/funSimAvg"}
    other = PhenotypeRank(RankDiseases(hpo, "lin", "funSimAvg"))
    assert other.name == "phenotype-rank (lin/funSimAvg)"

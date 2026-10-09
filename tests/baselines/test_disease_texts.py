"""B0c, diseases of the best-matching texts, on the miniature texts."""

from collections.abc import Callable

from raredx.baselines.disease_texts import DiseaseTextsRank
from raredx.data.cases import Case
from raredx.evals.systems import question_of
from raredx.knowledge.hpo import HPO
from raredx.knowledge.text_index import TextIndex
from raredx.tools.search_disease_texts import SearchDiseaseTexts


def test_the_findings_as_words_find_the_disease_described_with_them(
    hpo: HPO, text_index: TextIndex, make_case: Callable[..., Case]
) -> None:
    system = DiseaseTextsRank(SearchDiseaseTexts(text_index, hpo))
    case = make_case(
        "q", hpo_ids=["HP:0000510"], hpo_labels=["Rod-cone dystrophy", "Night blindness"]
    )
    answers = system.predict(question_of(case))
    assert answers[0].disease_id == "OMIM:690002"
    assert answers[0].disease_name == "Hearing-retina syndrome"  # HPO's name for it
    ids = [c.disease_id for c in answers]
    assert len(ids) == len(set(ids))


def test_a_run_records_the_index(hpo: HPO, text_index: TextIndex) -> None:
    text_index.info.update(passages=4, dense="d", sparse="s")
    params = DiseaseTextsRank(SearchDiseaseTexts(text_index, hpo)).params()
    assert params["text_index"] == "test texts; 4 passages"

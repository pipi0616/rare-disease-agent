"""B0b, diseases of the most similar patients, on a small bank."""

from collections.abc import Callable

from raredx.baselines.similar_patients import SimilarPatientsRank
from raredx.data.cases import Case
from raredx.evals.systems import question_of
from raredx.knowledge.hpo import HPO
from raredx.tools.find_similar_patients import FindSimilarPatients


def test_each_disease_appears_once_in_the_order_of_its_nearest_patient(
    hpo: HPO, patients: list[Case], make_case: Callable[..., Case]
) -> None:
    system = SimilarPatientsRank(FindSimilarPatients(hpo, patients, "test bank"))
    case = make_case("q", hpo_ids=["HP:0000407", "HP:0000786"], hpo_labels=["a", "b"])
    answers = system.predict(question_of(case))
    ids = [c.disease_id for c in answers]
    assert ids[0] == "OMIM:690001" and len(ids) == len(set(ids))
    assert answers[0].gene == "GENEA"  # the nearest patient's gene


def test_a_run_records_the_bank(hpo: HPO, patients: list[Case]) -> None:
    system = SimilarPatientsRank(FindSimilarPatients(hpo, patients, "test bank"))
    assert system.name == "similar-patients"
    assert system.params()["patient_bank"] == "test bank"

"""The similar-case-reports route, over a few reports indexed with the stand-in embedder."""

from typing import Any

from raredx.knowledge.case_bank import CaseBank, Report
from raredx.knowledge.text_index import TextIndex

REPORTS = [
    Report(id="r1", pmid="PMID:1", disease_id="ORPHA:117", text="oral ulcers uveitis arthritis"),
    Report(id="r2", pmid="PMID:2", disease_id="ORPHA:117", text="oral ulcers uveitis skin lesions"),
    Report(
        id="r3", pmid="PMID:3", disease_id="ORPHA:81", text="myositis interstitial lung disease"
    ),
    Report(id="r4", pmid="PMID:4", disease_id="ORPHA:536", text="malar rash arthritis ulcers"),
]


def bank(embedder: Any) -> CaseBank:
    dense, sparse = embedder.passages([r.text for r in REPORTS])
    return CaseBank(TextIndex(REPORTS, dense, sparse, embedder, {}))


def test_the_diagnoses_of_the_most_similar_reports_come_first_each_once(word_embedder: Any) -> None:
    found = bank(word_embedder).nominate(["Oral ulcers", "Uveitis"], own_paper=None, k=3)
    assert found[0] == "ORPHA:117" and len(found) == len(set(found))


def test_a_report_from_the_patients_own_paper_is_never_returned(word_embedder: Any) -> None:
    cases = bank(word_embedder)
    assert all(r.pmid != "PMID:1" for r in cases.similar(["Oral ulcers", "Uveitis"], "PMID:1"))
    # Behçet still comes first: another paper reports it too
    assert cases.nominate(["Oral ulcers", "Uveitis"], "PMID:1")[0] == "ORPHA:117"

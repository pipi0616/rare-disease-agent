"""Chapter 33's retrieval measures, on hand-made passages."""

from pathlib import Path

from raredx.evals import rag
from raredx.knowledge.texts import Passage


def passage(text: str, diseases: list[str], parent: str = "") -> Passage:
    return Passage(text=text, disease_ids=diseases, disease_name="", source="", parent=parent)


def question(kind: rag.Kind, answer: list[str]) -> rag.Question:
    return rag.Question(
        kind=kind,
        source="s",
        case_id="c",
        text="q",
        disease="OMIM:1",
        accepted=["OMIM:1", "ORPHA:1"],
        answer=answer,
        hide_pmids=[],
        hide_diseases=[],
    )


def test_a_fact_counts_only_from_a_passage_about_the_disease_saying_it() -> None:
    q = question("inheritance", [rag.INHERITANCE["Autosomal recessive"]])
    found = [
        passage("Another disease is autosomal recessive.", ["OMIM:2"]),
        passage("It is described in children.", ["OMIM:1"]),
        passage("small piece", ["OMIM:1"], parent="Inherited in an autosomal-recessive manner."),
    ]
    assert rag.score(q, found) == {"about@5": 1.0, "answer@5": 1.0, "rr": 1 / 3}
    assert rag.score(q, found[:2])["answer@5"] == 0.0


def test_find_credits_diseases_by_rank_shared_among_a_passages_diseases() -> None:
    q = question("find", [])
    found = [passage("a", ["OMIM:9", "OMIM:8"])] * 3 + [passage("b", ["ORPHA:1"])]
    assert rag.score(q, found) == {"disease@10": 1.0, "passage@10": 1.0}


def test_orphanets_inheritance_is_read_where_a_text_can_say_it(tmp_path: Path) -> None:
    xml = tmp_path / "ages.xml"
    xml.write_text(
        "<JDBOR><DisorderList>"
        "<Disorder><OrphaCode>1</OrphaCode><TypeOfInheritanceList><TypeOfInheritance>"
        "<Name>Autosomal recessive</Name></TypeOfInheritance></TypeOfInheritanceList></Disorder>"
        "<Disorder><OrphaCode>2</OrphaCode><TypeOfInheritanceList><TypeOfInheritance>"
        "<Name>Unknown</Name></TypeOfInheritance></TypeOfInheritanceList></Disorder>"
        "</DisorderList></JDBOR>",
        encoding="utf-8",
    )
    assert rag.inheritance_key(xml) == {"ORPHA:1": ["Autosomal recessive"]}


def test_two_runs_are_compared_question_by_question() -> None:
    def rows(hits: list[float]) -> list[dict[str, object]]:
        return [
            {"kind": "feature", "source": "s", "question": str(i), "scores": {"answer@5": h}}
            for i, h in enumerate(hits)
        ]

    only_a, only_b, p = rag.paired(rows([1, 1, 1, 0]), rows([0, 0, 1, 1]), "feature", "answer@5")
    assert (only_a, only_b) == (2, 1) and 0 < p <= 1

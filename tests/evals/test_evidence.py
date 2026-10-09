"""Reading an agent's evidence back from a recorded trace (a stand-in trace, no MLflow)."""

from types import SimpleNamespace
from typing import Any

from raredx.evals.evidence import gather


def span(name: str, outputs: Any, t: int, kind: str = "TOOL", inputs: Any = None) -> Any:
    return SimpleNamespace(
        name=name, span_type=kind, outputs=outputs, inputs=inputs or {}, start_time_ns=t
    )


def finding(label: str) -> dict[str, str]:
    return {"hpo_id": "HP:0000001", "label": label}


def recorded_case() -> Any:
    root = span(
        "seeded-agent",
        {
            "candidates": [
                {"disease_id": "OMIM:690002", "disease_name": "B", "reason": "agent likes B"},
                {"disease_id": "OMIM:690001", "disease_name": "A", "reason": "then A"},
            ]
        },
        0,
        kind="CHAIN",
        inputs={"question": {"case_id": "case-1"}},
    )
    ranking = {
        "matches": [
            {"disease_id": "OMIM:690001", "disease_name": "A", "genes": ["GENEA"], "score": 3},
            {"disease_id": "OMIM:690002", "disease_name": "B", "genes": [], "score": 2},
            {"disease_id": "OMIM:690003", "disease_name": "C", "genes": [], "score": 1},
        ]
    }
    check_a = {
        "disease_id": "OMIM:690001",
        "disease_name": "A",
        "n_findings": 2,
        "explained": [
            {"finding": finding("SNHL"), "feature": "SNHL", "relation": "same", "frequency": "3/4"},
            {
                "finding": finding("Bilateral SNHL"),
                "feature": "SNHL",
                "relation": "more specific",
                "frequency": None,
            },
        ],
        "unexplained": [],
        "contradicted": [],
        "missing": [{"feature": finding("Amenorrhea"), "frequency": "4/4"}],
    }
    check_b = {
        "disease_id": "OMIM:690002",
        "disease_name": "B",
        "n_findings": 2,
        "explained": [],
        "unexplained": [finding("SNHL"), finding("Bilateral SNHL")],
        "contradicted": [{"finding": finding("SNHL"), "frequency": "0/3"}],
        "missing": [],
    }
    similar = {
        "patients": [
            {
                "disease_id": "OMIM:690001",
                "disease_name": "A",
                "similarity": 4.1,
                "source": "PMID:1",
            },
            {
                "disease_id": "OMIM:690001",
                "disease_name": "A",
                "similarity": 3.9,
                "source": "PMID:2",
            },
            {
                "disease_id": "OMIM:690009",
                "disease_name": "Z",
                "similarity": 2.0,
                "source": "PMID:3",
            },
        ]
    }
    texts = {
        "hits": [
            {"disease_ids": ["OMIM:690001"], "disease_name": "A", "source": "Orphanet ORPHA:1"}
        ]
    }
    return SimpleNamespace(
        data=SimpleNamespace(
            spans=[
                root,
                span("rank_diseases", ranking, 1),
                span("check_match", check_a, 2),
                span("check_match", check_b, 3),
                span("find_similar_patients", similar, 4),
                span("find_similar_patients", similar, 5),  # searched twice: counted once
                span("find_similar_patients", '{"as": "text"}', 6),  # LangChain's copy: ignored
                span("search_disease_texts", texts, 7),
            ]
        )
    )


def test_each_candidate_gathers_the_evidence_every_tool_gave() -> None:
    evidence = gather(recorded_case())
    assert evidence.case_id == "case-1"
    a = next(c for c in evidence.candidates if c.disease_id == "OMIM:690001")
    assert a.phenotype_rank == 1 and a.genes == ["GENEA"]
    assert a.explained == ["SNHL (3/4)", "Bilateral SNHL (as SNHL, frequency unknown)"]
    assert a.missing == ["Amenorrhea (4/4)"]
    assert (a.similar_patients, a.similar_papers, a.patients_retrieved) == (2, 2, 3)
    assert a.text_sources == ["Orphanet ORPHA:1"]
    assert (a.agent_rank, a.agent_reason) == (2, "then A")
    b = next(c for c in evidence.candidates if c.disease_id == "OMIM:690002")
    assert b.contradicted == ["SNHL (0/3)"] and b.agent_rank == 1


def test_candidates_are_ordered_by_the_evidence_not_by_the_agent() -> None:
    ids = [c.disease_id for c in gather(recorded_case()).candidates]
    # A explains two findings; B none, though the agent put B first. C was only ranked,
    # and Z only one similar patient had: neither is judged again.
    assert ids == ["OMIM:690001", "OMIM:690002"]

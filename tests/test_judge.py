"""The judge, on stand-in evidence and a fake model: no network, no cost."""

import json
from typing import Any

import mlflow
import pytest

from raredx.evals.evidence import CandidateEvidence, CaseEvidence
from raredx.evals.systems import Candidate, Question
from raredx.judge import EvidenceJudge

QUESTION = Question(case_id="c1", hpo_ids=["HP:0000407"], hpo_labels=["SNHL"], sex="FEMALE")
EVIDENCE = CaseEvidence(
    case_id="c1",
    candidates=[
        CandidateEvidence(
            disease_id="OMIM:690001",
            disease_name="A",
            n_findings=1,
            explained=["SNHL (3/4)"],
            similar_patients=3,
            similar_papers=2,
            patients_retrieved=10,
            genes=["GENEA"],
            agent_rank=2,
            agent_reason="A fits",
        ),
        CandidateEvidence(
            disease_id="OMIM:690002",
            disease_name="B",
            n_findings=1,
            unexplained=["SNHL"],
            agent_rank=1,
            agent_reason="B fits better",
        ),
    ],
)
AGENT = [
    Candidate(disease_name="B", disease_id="OMIM:690002"),
    Candidate(disease_name="A", disease_id="OMIM:690001"),
    Candidate(disease_name="C", disease_id="OMIM:690003", reason="filled"),
]


def judge(fake_llm: Any, reply: dict[str, Any], variant: str = "table") -> tuple[Any, Any]:
    client = fake_llm(json.dumps(reply))
    system = EvidenceJudge(
        client, "deepseek-flash", {"c1": EVIDENCE}, {"c1": AGENT}, "run-1", variant
    )
    return system, client


def test_the_judge_ranks_the_table_and_fills_from_the_agents_answer(fake_llm: Any) -> None:
    reply = {
        "ranking": [
            {"disease_id": "OMIM:690001", "reason": "three similar patients"},
            {"disease_id": "OMIM:699999", "reason": "not in the table"},
        ]
    }
    system, client = judge(fake_llm, reply)
    answers = system.predict(QUESTION)
    assert [c.disease_id for c in answers] == ["OMIM:690001", "OMIM:690002", "OMIM:690003"]
    assert answers[0].reason == "three similar patients" and answers[0].gene == "GENEA"
    prompt = client.requests[0]["messages"][1]["content"]
    assert "similar published patients: 3 of the 10 most similar, from 2 paper(s)" in prompt
    assert "B fits better" not in prompt  # the table variant does not see the agent's view


def test_the_review_variant_sees_the_agents_ranking(fake_llm: Any) -> None:
    reply = {"ranking": [{"disease_id": "OMIM:690002", "reason": "kept"}]}
    system, client = judge(fake_llm, reply, variant="review")
    system.predict(QUESTION)
    prompt = client.requests[0]["messages"][1]["content"]
    assert "1. OMIM:690002 B: B fits better" in prompt
    assert system.params()["prompt_version"] == "judge-review-v1"


def test_what_the_judge_reads_is_recorded_for_the_leak_audit(fake_llm: Any) -> None:
    system, _ = judge(fake_llm, {"ranking": [{"disease_id": "OMIM:690001", "reason": "x"}]})
    system.predict(QUESTION)
    mlflow.flush_trace_async_logging()
    trace = mlflow.get_trace(mlflow.get_last_active_trace_id() or "")
    assert trace is not None
    spans = {s.name: s for s in trace.data.spans}
    assert spans["recorded_evidence"].span_type == "TOOL"


def test_an_unknown_variant_is_refused(fake_llm: Any) -> None:
    with pytest.raises(ValueError, match="table, review"):
        EvidenceJudge(fake_llm("{}"), "m", {}, {}, "run-1", "vote")

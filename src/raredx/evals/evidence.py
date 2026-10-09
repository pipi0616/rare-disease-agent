"""The evidence an agent gathered for one case, read back from its recorded trace.

An agent run records every tool call it made, with its output. Read back, those
outputs are the evidence it had when it answered: per candidate disease, where
the phenotype ranking put it, what checking it against the patient found, how
many of the most similar published patients had it, whether a disease text
described it, its genes and inheritance.

Laid out as one row per candidate, the evidence can be judged again — by a
different prompt, or a different way of deciding — with one model call per case
and no tool called again. That is how changes to the final judgment are tried
cheaply (replay), before one of them is built into the agent and run in full.

Only the tools' own spans are read (their outputs are the tools' models, as
dicts); LangChain's wrappers around them hold the same output as a message.
"""

from typing import Any

from pydantic import BaseModel

MAX_CANDIDATES = 15


class CandidateEvidence(BaseModel):
    disease_id: str
    disease_name: str
    phenotype_rank: int | None = None  # in the phenotype ranking (1 = best), if it was there
    n_findings: int | None = None
    explained: list[str] = []  # "finding (frequency)" or "finding (as feature, frequency)"
    unexplained: list[str] = []
    contradicted: list[str] = []  # "finding (0/3)": its patients were checked and lacked it
    missing: list[str] = []  # frequent features of the disease the patient lacks
    similar_patients: int = 0  # among the most similar published patients retrieved
    similar_papers: int = 0  # how many different papers those patients come from
    patients_retrieved: int = 0  # how many patients the similar-patient searches returned
    text_sources: list[str] = []  # disease texts the agent read about it
    genes: list[str] = []
    inheritance: list[str] = []
    onset_and_course: list[str] = []
    agent_rank: int | None = None  # where the agent itself put it
    agent_reason: str | None = None


class CaseEvidence(BaseModel):
    case_id: str
    candidates: list[CandidateEvidence]


def _tool_outputs(trace: Any) -> list[tuple[str, dict[str, Any]]]:
    return [
        (span.name, span.outputs)
        for span in sorted(trace.data.spans, key=lambda s: s.start_time_ns)
        if span.span_type == "TOOL"
        and isinstance(span.outputs, dict)
        and "additional_kwargs" not in span.outputs  # LangChain's ToolMessage, a copy
    ]


def _explained(e: dict[str, Any]) -> str:
    frequency = e.get("frequency") or "frequency unknown"
    label = e["finding"]["label"]
    if e.get("relation") == "same":
        return f"{label} ({frequency})"
    return f"{label} (as {e['feature']}, {frequency})"


def gather(trace: Any) -> CaseEvidence:
    """The evidence in one recorded case, one row per candidate disease."""
    rows: dict[str, CandidateEvidence] = {}

    def row(disease_id: str, name: str) -> CandidateEvidence:
        if disease_id not in rows:
            rows[disease_id] = CandidateEvidence(disease_id=disease_id, disease_name=name)
        return rows[disease_id]

    patients: dict[str, set[str]] = {}
    for name, out in _tool_outputs(trace):
        if name == "rank_diseases":
            for i, m in enumerate(out.get("matches", []), 1):
                r = row(m["disease_id"], m["disease_name"])
                r.phenotype_rank = min(r.phenotype_rank or i, i)
                r.genes = r.genes or list(m.get("genes", []))
        elif name == "check_match":
            r = row(out["disease_id"], out["disease_name"])
            r.n_findings = out.get("n_findings")
            r.explained = [_explained(e) for e in out.get("explained", [])]
            r.unexplained = [f["label"] for f in out.get("unexplained", [])]
            r.contradicted = [
                f"{c['finding']['label']} ({c.get('frequency', '0')})"
                for c in out.get("contradicted", [])
            ]
            r.missing = [
                f"{m['feature']['label']} ({m.get('frequency', '')})"
                for m in out.get("missing", [])[:3]
            ]
        elif name == "lookup_disease":
            r = row(out["disease_id"], out["disease_name"])
            r.genes = list(out.get("genes", [])) or r.genes
            r.inheritance = list(out.get("inheritance", []))
            r.onset_and_course = list(out.get("onset_and_course", []))
        elif name == "find_similar_patients":
            found = out.get("patients", [])
            for p in found:
                row(p["disease_id"], p["disease_name"])
                patients.setdefault(p["disease_id"], set()).add(f"{p['source']}|{p['similarity']}")
            for r in rows.values():
                r.patients_retrieved = max(r.patients_retrieved, len(found))
        elif name == "search_disease_texts":
            for hit in out.get("hits", []):
                for disease_id in hit.get("disease_ids", []):
                    r = row(disease_id, hit.get("disease_name", disease_id))
                    if hit["source"] not in r.text_sources:
                        r.text_sources.append(hit["source"])
    retrieved = max((r.patients_retrieved for r in rows.values()), default=0)
    for disease_id, seen in patients.items():
        r = rows[disease_id]
        r.similar_patients = len(seen)
        r.similar_papers = len({s.split("|")[0] for s in seen})
    for r in rows.values():
        r.patients_retrieved = retrieved

    answer = (trace.data.spans[0].outputs or {}).get("candidates", [])
    for i, c in enumerate(answer, 1):
        if c.get("disease_id"):
            r = row(c["disease_id"], c.get("disease_name", c["disease_id"]))
            r.agent_rank = r.agent_rank or i
            r.agent_reason = r.agent_reason or c.get("reason")

    case_id = trace.data.spans[0].inputs["question"]["case_id"]
    return CaseEvidence(case_id=case_id, candidates=_shortlist(list(rows.values())))


def _shortlist(rows: list[CandidateEvidence]) -> list[CandidateEvidence]:
    """The candidates worth judging, at most MAX_CANDIDATES: those checked against the
    patient, named by the agent, or shared by two or more similar patients — ordered
    by the evidence alone (findings explained, then the phenotype ranking), never by
    the agent's own preference."""
    kept = [
        r
        for r in rows
        if r.n_findings is not None or r.agent_rank is not None or r.similar_patients >= 2
    ]
    kept.sort(
        key=lambda r: (
            -len(r.explained),
            r.phenotype_rank or 10_000,
            -r.similar_patients,
            r.disease_id,
        )
    )
    shortlist = kept[:MAX_CANDIDATES]
    for r in kept[MAX_CANDIDATES:]:  # the agent's own top five are always judged again
        if r.agent_rank is not None and r.agent_rank <= 5:
            shortlist.append(r)
    return shortlist

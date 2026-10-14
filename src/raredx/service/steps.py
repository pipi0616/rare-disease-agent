"""An agent's events in words: the line a person watching reads for each step.

Written here once, on the server, so every client — the demo page, a script, a
log — shows the same account of what the agent did.
"""

from collections import Counter
from typing import Any

from raredx.service.schemas import StepKind
from raredx.service.watch import Event, ModelTurn, ToolResult

FINAL_ANSWER = "FinalAnswer"  # the agent's answer arrives as a call to this schema
LEADING = 3


def _first(items: list[str]) -> str:
    return "; ".join(items[:LEADING])


def _tool(result: ToolResult) -> tuple[str, str | None]:
    tool, args, out = result.tool, result.arguments, result.output
    if result.error is not None:
        return f"{tool}: could not answer", result.error
    if not isinstance(out, dict):
        return tool, None
    if tool == "rank_diseases":
        names = [m["disease_name"] for m in out.get("matches", [])]
        return "rank_diseases: every disease ranked by phenotype", f"Leading: {_first(names)}"
    if tool == "check_match":
        detail = f"explains {len(out.get('explained', []))} of {out.get('n_findings')} findings"
        if out.get("contradicted"):
            detail += f"; {len(out['contradicted'])} recorded absent in its patients"
        return f"check_match: {out.get('disease_name', args.get('disease_id'))}", detail
    if tool == "lookup_disease":
        parts = [f"{out.get('n_features', 0)} features"]
        parts += out.get("inheritance", [])
        if out.get("genes"):
            parts.append("genes " + ", ".join(out["genes"][:LEADING]))
        return f"lookup_disease: {out.get('disease_name', args.get('disease_id'))}", "; ".join(
            parts
        )
    if tool == "find_disease":
        names = [f"{m['disease_name']} ({m['disease_id']})" for m in out.get("matches", [])]
        return f"find_disease: “{args.get('name', '')}”", f"Closest: {_first(names)}"
    if tool == "find_similar_patients":
        patients = out.get("patients", [])
        shared = Counter(p["disease_name"] for p in patients).most_common(LEADING)
        detail = f"{len(patients)} closest of {out.get('searched', 0):,} published patients"
        if shared:
            detail += ": " + "; ".join(f"{name} ×{n}" for name, n in shared)
        return "find_similar_patients: published patients like this one", detail
    if tool == "rank_candidate_genes":
        genes = [
            f"{g['gene']} ({g['diseases'][0]['disease_name']})"
            for g in out.get("genes", [])
            if g.get("diseases")
        ]
        return "rank_candidate_genes: the candidate genes ranked by phenotype", (
            f"Leading: {_first(genes)}" if genes else "None of them has a known disease"
        )
    if tool == "search_disease_texts":
        names = [h.get("disease_name", "") for h in out.get("hits", [])]
        return f"search_disease_texts: “{args.get('query', '')}”", f"Found: {_first(names)}"
    return tool, None


def _turn(turn: ModelTurn) -> tuple[str, str | None]:
    asked = Counter(name for name, _ in turn.calls)
    if FINAL_ANSWER in asked:
        answer: dict[str, Any] = next(args for name, args in turn.calls if name == FINAL_ANSWER)
        diagnoses = answer.get("diagnoses") or []
        first = diagnoses[0].get("disease_name") if diagnoses else None
        return (
            f"Model, turn {turn.turn}: gives its answer",
            f"{len(diagnoses)} diagnoses, first: {first}" if first else None,
        )
    if not asked:
        return f"Model, turn {turn.turn}: no tool asked for", None
    wanted = ", ".join(name if n == 1 else f"{name} ×{n}" for name, n in asked.items())
    return f"Model, turn {turn.turn}: asks the tools", wanted


def describe(event: Event) -> tuple[StepKind, str, str | None]:
    """An event as the kind, title and detail of a Step."""
    if isinstance(event, ModelTurn):
        title, detail = _turn(event)
        return "model", title, detail
    title, detail = _tool(event)
    return "tool", title, detail

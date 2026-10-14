"""The demo page: a form over the API, and the agent's steps as they happen.

Three ways in: a published patient's findings; HPO terms of one's own; or, where
the service reads notes, a clinical note — read into terms, which the user
checks before they are sent.

Run with `raredx demo` (Streamlit), beside a running `raredx serve`. The page
holds no logic of its own: it calls the service through the typed client, as
another team's front end would, and shows what comes back. Everything on it is
in the API's answer.
"""

import html
import os
import re
from typing import Any

import httpx2
import streamlit as st
from pydantic import ValidationError

from raredx.phenotyping.reader import Finding as NoteFinding
from raredx.service.client import Client, ServiceError
from raredx.service.schemas import (
    DISCLAIMER,
    DiagnoseRequest,
    DiagnoseResponse,
    Diagnosis,
    Example,
    NoteResponse,
    Step,
    SystemInfo,
)

API_URL = os.environ.get("RAREDX_API_URL", "http://127.0.0.1:8000")
OWN = "Enter a patient"
NOTE = "Start from a clinical note"
BLANK = "a blank page"
# How a finding's words are marked in the note: the patient has it, the note denies it,
# a relative has it.
MARKED = {
    "present": "background:#c3f0ca",
    "absent": "background:#e5e7eb;text-decoration:line-through",
    "family": "background:#cfe4ff",
}
MARK = {"tools": "🧰", "model": "🧠", "tool": "🔎", "answer": "✅", "fallback": "⚠️"}

# The held-out evaluation of v1.0 (docs/heldout_plan.md, section 8): 840 cases, one per paper.
MEASURED = """\
| 840 held-out cases | top-1 | top-10 |
|---|---|---|
| agent | 42.4% | 62.0% |
| fallback (no model) | 32.1% | 51.5% |
| agent, with candidate genes | 65.9% | 81.4% |
| fallback, with candidate genes | 59.5% | 80.0% |
"""


@st.cache_resource
def client() -> Client:
    return Client(API_URL, api_key=os.environ.get("RAREDX_SERVICE_API_KEY"))


def sidebar(system: SystemInfo) -> None:
    with st.sidebar:
        st.subheader("What is serving")
        agent = system.agent
        if agent is None:
            st.warning(f"No model: {system.unavailable_because}. Answers are the fallback's.")
            st.markdown(f"- Fallback: `{system.fallback['without_candidate_genes']}`")
        else:
            st.markdown(
                f"- Model: `{agent['model']}`, at most {agent['max_model_calls']} calls\n"
                f"- Prompt: `{agent['prompt_version']}`\n"
                f"- Tools: {', '.join(f'`{t}`' for t in agent['tools'].split(', '))}\n"
                f"- Knowledge: HPO {agent['hpo_release']}\n"
                f"- Patient bank: {agent.get('patient_bank', 'none')}"
            )
        if system.note_reader:
            reader = system.note_reader
            st.markdown(
                f"- Notes read by: `{reader['model']}`, prompt `{reader['prompt_version']}`, "
                f"terms from HPO {reader['hpo_release']}"
            )
        st.caption(f"service {system.service_version} · code {system.code}")
        st.subheader("Measured")
        st.markdown(MEASURED)
        st.caption(
            "Recall of the published diagnosis, v1.0, each case's own paper left out. "
            "Plan and results: docs/heldout_plan.md."
        )
        st.subheader("Not a medical device")
        st.caption(DISCLAIMER)


def _forget_answer() -> None:
    st.session_state.pop("answer", None)


def _forget_note() -> None:
    _forget_answer()
    st.session_state.pop("note", None)


def _add_term(hpo_id: str) -> None:
    written = st.session_state.get("own_terms", "").strip()
    st.session_state["own_terms"] = f"{written}\n{hpo_id}".strip()


def example_request(example: Example) -> DiagnoseRequest:
    st.markdown(
        f"**Published patient** ({example.source}) · sex: {example.request.sex} · "
        f"{len(example.findings)} findings"
    )
    st.markdown("\n".join(f"- {f.label} `{f.hpo_id}`" for f in example.findings))
    st.caption(
        "Sent as in the evaluation: the patient's own paper is left out of the knowledge "
        "(`exclude_sources`), so the answer has to be reasoned, not read."
    )
    with_genes = example.candidate_genes is not None and st.checkbox(
        "Add a sequencing result (simulated, as in the evaluation: the causal gene "
        f"among {len(example.candidate_genes) - 1} decoys)",
        on_change=_forget_answer,
    )
    genes = example.candidate_genes if with_genes else None
    return example.request.model_copy(update={"candidate_genes": genes})


def own_request() -> DiagnoseRequest | None:
    left, right = st.columns([3, 2])
    with left:
        terms = st.text_area(
            "Findings, as HPO term ids", key="own_terms", height=160, placeholder="HP:0000407"
        )
        sex = st.radio("Sex", ["unknown", "female", "male"], horizontal=True)
        genes = st.text_input("Candidate genes from sequencing (optional)", placeholder="GJB2")
        excluded = st.text_input(
            "Publications to leave out (optional)",
            placeholder="PMID:12345678",
            help="For a patient who was published: with their own report in the knowledge, "
            "the answer is read, not reasoned.",
        )
    with right:
        query = st.text_input("Find a term by name", placeholder="hearing")
        if len(query.strip()) >= 2:
            for term in client().terms(query.strip(), limit=8):
                st.button(
                    f"{term.label} · {term.hpo_id}",
                    key=f"add-{term.hpo_id}",
                    on_click=_add_term,
                    args=(term.hpo_id,),
                )
    hpo_ids = re.findall(r"HP:\d{7}", terms)
    if not hpo_ids:
        return None
    try:
        return DiagnoseRequest.model_validate(
            {
                "hpo_ids": hpo_ids,
                "sex": sex,
                "candidate_genes": re.findall(r"[A-Za-z0-9][A-Za-z0-9.-]*", genes) or None,
                "exclude_sources": [f"PMID:{n}" for n in re.findall(r"\d+", excluded)],
            }
        )
    except ValidationError as e:
        st.error("; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()))
        return None


def marked(text: str, findings: list[NoteFinding]) -> str:
    """The note as HTML, each finding's words marked by what the note says of them.
    Every part of the note is escaped: whatever is pasted is shown as text."""
    spans = sorted((f.start, f.end, f.status) for f in findings if f.start is not None and f.end)
    parts, at = [], 0
    for start, end, status in spans:
        if start < at:  # inside words already marked
            continue
        parts.append(html.escape(text[at:start]))
        style = f"{MARKED[status]};color:#111;border-radius:4px;padding:1px 3px"
        parts.append(f'<span style="{style}">{html.escape(text[start:end])}</span>')
        at = end
    parts.append(html.escape(text[at:]))
    return f"<div style='white-space:pre-wrap;line-height:1.9'>{''.join(parts)}</div>"


def note_request(examples: list[Example]) -> tuple[DiagnoseRequest | None, Example | None]:
    """A note, read into terms the user checks; the request they make, and the published
    patient the note was written from, if it was."""
    noted = {f"{e.title} · {e.source}": e for e in examples if e.note}
    start = st.radio("Start from", [*noted, BLANK], horizontal=True, on_change=_forget_note)
    example = noted.get(start)
    text = (
        st.text_area(
            "Clinical note", value=example.note if example else "", height=230, key=f"text-{start}"
        )
        or ""
    )
    st.caption(
        ("Written for this demo from the published patient's findings, in a clinician's "
         "words: not a real note. " if example else "")
        + "The note is sent to the model provider to be read, and kept nowhere by the "
        "service. Never paste a real patient's note here."
    )  # fmt: skip
    if st.button(
        "Read the note", key="read_note", disabled=not text.strip(), on_click=_forget_answer
    ):
        with st.spinner("Reading the note …"):
            try:
                read = client().read_note(text)
            except ServiceError as e:
                st.error(f"Refused ({e.status_code}): {e.detail}")
                return None, example
        st.session_state["note"] = (text, read.model_dump_json())
    if "note" not in st.session_state:
        return None, example
    read_text, answer = st.session_state["note"]
    read = NoteResponse.model_validate_json(answer)
    st.markdown(marked(read_text, read.findings), unsafe_allow_html=True)
    st.caption(
        "Marked: what the patient has · ~~what the note denies~~ · what a relative has. "
        f"Read with {read.usage.model_calls} model calls in {read.usage.seconds:.1f} s, "
        f"about ${read.usage.cost_usd_estimate:.4f}. {read.notice}"
    )
    rows: list[dict[str, Any]] = [
        {
            "Send": f.status == "present" and f.hpo_id is not None,
            "The note says": {"present": "has it", "absent": "denies it", "family": "a relative"}[
                f.status
            ],
            "Term": f.label or f"— ({f.uncoded})",
            "HPO": f.hpo_id or "",
            "In the note's words": f.quote,
            "Coded by": f.coded_by or "",
        }
        for f in read.findings
    ]
    edited = st.data_editor(
        rows,
        hide_index=True,
        disabled=["The note says", "Term", "HPO", "In the note's words", "Coded by"],
        key=f"terms-{answer[:40]}",
    )
    chosen = list(dict.fromkeys(r["HPO"] for r in edited if r["Send"] and r["HPO"]))
    st.caption(f"{len(chosen)} terms ticked: they are what is sent to diagnose, codes only.")
    if not chosen:
        return None, example
    sex = example.request.sex if example else "unknown"
    excluded = [example.source] if example else []  # as in the evaluation: its paper left out
    return DiagnoseRequest(hpo_ids=chosen, sex=sex, exclude_sources=excluded), example


def show_step(step: Step) -> None:
    line = f"{MARK[step.kind]} `{step.seconds:5.1f} s` **{step.title}**"
    st.markdown(line + (f"  \n{step.detail}" if step.detail else ""))


def ask(request: DiagnoseRequest) -> DiagnoseResponse | None:
    """Send the request and show each step as the service reports it."""
    answer: DiagnoseResponse | None = None
    with st.status("Working …", expanded=True) as status:
        try:
            for item in client().stream(request):
                if isinstance(item, Step):
                    show_step(item)
                else:
                    answer = item
        except ServiceError as e:
            status.update(label=f"Refused ({e.status_code})", state="error")
            st.error(str(e.detail))
            return None
        except httpx2.HTTPError as e:
            status.update(label="The service did not answer", state="error")
            st.error(f"{type(e).__name__}: {e}")
            return None
        status.update(label="Done", state="complete", expanded=False)
    return answer


def show_evidence(d: Diagnosis) -> None:
    number = d.disease_id.removeprefix("OMIM:")
    st.markdown(f"[{d.disease_id}](https://omim.org/entry/{number})" + f" · {d.reason or ''}")
    if d.evidence is None:
        st.caption("HPO has no annotation of this disease to check the patient against.")
        return
    e, m = d.evidence, d.evidence.match
    facts = [", ".join(e.inheritance), ", ".join(e.onset_and_course)]
    if e.genes:
        facts.append("genes: " + ", ".join(e.genes))
    st.caption(" · ".join(f for f in facts if f))
    if m.explained:
        st.markdown(f"**Explains {len(m.explained)} of {m.n_findings} findings**")
        st.dataframe(
            [
                {
                    "Finding": x.finding.label,
                    "Feature of the disease": x.feature,
                    "The finding is": x.relation,
                    "How often": x.frequency or "not recorded",
                    "Sources": ", ".join(x.sources),
                }
                for x in m.explained
            ],
            hide_index=True,
        )
    if m.unexplained:
        st.markdown("**Does not explain:** " + "; ".join(f.label for f in m.unexplained))
    if m.contradicted:
        st.markdown(
            "**Recorded absent in its patients:** "
            + "; ".join(f"{c.finding.label} ({c.frequency})" for c in m.contradicted)
        )
    if m.missing:
        lacking = "; ".join(f"{x.feature.label} ({x.frequency})" for x in m.missing[:5])
        st.markdown(f"**Frequent features the patient lacks ({m.n_missing}):** {lacking}")


def show(answer: DiagnoseResponse, example: Example | None) -> None:
    usage = answer.usage
    if answer.mode == "agent":
        st.success(
            f"Answered by the agent: {usage.model_calls} model calls, {usage.seconds:.1f} s, "
            f"{usage.input_tokens + usage.output_tokens:,} tokens, "
            f"about ${usage.cost_usd_estimate:.4f}."
        )
    else:
        st.warning(
            f"Answered without the model — {answer.fallback_reason}. This is the tools' own "
            f"ranking ({usage.seconds:.1f} s): measured too, and weaker (see the sidebar)."
        )
    if example is not None:
        rank = next(
            (d.rank for d in answer.diagnoses if d.disease_id == example.confirmed_disease_id),
            None,
        )
        gene = f", gene {example.confirmed_gene}" if example.confirmed_gene else ""
        placed = f"ranked **#{rank}** here" if rank else "**not among these ten**"
        st.info(
            f"Published diagnosis ({example.source}): **{example.confirmed_disease_name}** "
            f"({example.confirmed_disease_id}{gene}) — {placed}.  \n"
            f"In the evaluation: {example.in_evaluation}"
        )
    st.dataframe(
        [
            {
                "#": d.rank,
                "Disease": d.disease_name,
                "OMIM": d.disease_id,
                "Gene": d.gene or "",
                "Findings explained": (
                    f"{len(d.evidence.match.explained)}/{d.evidence.match.n_findings}"
                    if d.evidence
                    else "—"
                ),
                "Why": d.reason or "",
            }
            for d in answer.diagnoses
        ],
        hide_index=True,
    )
    st.subheader("Evidence")
    for d in answer.diagnoses:
        with st.expander(f"{d.rank}. {d.disease_name}", expanded=d.rank == 1):
            show_evidence(d)
    with st.expander(f"How it got there ({len(answer.steps)} steps)"):
        for step in answer.steps:
            show_step(step)
    st.caption(
        f"request `{answer.request_id}` · trace `{answer.trace_id}` in the MLflow experiment "
        "“service”: every model call and tool call made for this answer is recorded there."
    )


def main() -> None:
    st.set_page_config(page_title="raredx", page_icon="🧬", layout="wide")
    st.title("raredx — a rare-disease diagnosis agent")
    st.caption(
        "A patient's findings in — as HPO terms, or a clinical note read into them; up to ten "
        "candidate diseases out, each with its reason and its evidence. " + DISCLAIMER
    )
    try:
        system, examples = client().system(), client().examples()
    except (httpx2.HTTPError, ServiceError) as e:
        st.error(
            f"The service at {API_URL} is not answering ({type(e).__name__}). "
            "Start it with `raredx serve`, then reload this page."
        )
        st.stop()
    sidebar(system)

    labels = {f"Example {i} · {e.title}": e for i, e in enumerate(examples, 1)}
    ways = [NOTE] if system.note_reader else []
    choice = st.selectbox("Patient", [*ways, *labels, OWN], on_change=_forget_note)
    example = labels.get(choice)
    if choice == NOTE:
        request, example = note_request(examples)
    else:
        request = example_request(example) if example else own_request()

    if st.button("Diagnose", key="diagnose", type="primary", disabled=request is None) and request:
        answer = ask(request)
        if answer is None:
            _forget_answer()
        else:
            st.session_state["answer"] = answer.model_dump_json()
    if "answer" in st.session_state:
        show(DiagnoseResponse.model_validate_json(st.session_state["answer"]), example)


if __name__ == "__main__":  # Streamlit runs the page as a script
    main()

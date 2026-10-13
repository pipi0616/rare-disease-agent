"""The demo page: a form over the API, and the agent's steps as they happen.

Run with `raredx demo` (Streamlit), beside a running `raredx serve`. The page
holds no logic of its own: it calls the service through the typed client, as
another team's front end would, and shows what comes back. Everything on it is
in the API's answer.
"""

import os
import re

import httpx2
import streamlit as st
from pydantic import ValidationError

from raredx.service.client import Client, ServiceError
from raredx.service.schemas import (
    DISCLAIMER,
    DiagnoseRequest,
    DiagnoseResponse,
    Diagnosis,
    Example,
    Step,
    SystemInfo,
)

API_URL = os.environ.get("RAREDX_API_URL", "http://127.0.0.1:8000")
OWN = "Enter a patient"
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
        "A patient's findings as HPO terms in; up to ten candidate diseases out, each with "
        "its reason and its evidence. " + DISCLAIMER
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
    choice = st.selectbox("Patient", [*labels, OWN], on_change=_forget_answer)
    example = labels.get(choice)
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

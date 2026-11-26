# ruff: noqa: E501  (long strings: addresses, cover-letter and checklist text)
"""Build the submission folders for three journals on three publishers' systems from docs/paper.

    uv run python scripts/build_journals.py

01_JMIR (JMIR Publications): the full manuscript in JMIR format (title page, structured
abstract, unnumbered IMRD sections, figures and tables inline, P values in JMIR style recomputed
from the paired counts, AMA references) with Multimedia Appendices.

02_Journal_of_Medical_Systems (Springer Nature) and 03_BMJ_Health_and_Care_Informatics (BMJ):
shorter texts written for their word limits (journal_sources/joms_body.md, bmj_body.md), with
their own front and end matter, reference styles, figure and table labels, supplementary files
(PDF) and figure files (EPS/PDF and 600-dpi TIFF).

Reads docs/paper/{manuscript,supplementary,references}.md and docs/paper/journal_sources/ and
writes docs/paper/journals/<NN_Journal>/ (not tracked by git), each with a cover letter, a
pre-submission checklist and checksums. Every number in the shorter texts must appear in
manuscript.md or supplementary.md (checked here), and every p value attached to a paired count
is checked against the exact sign test.
"""

import hashlib
import re
import shutil
import subprocess
from functools import lru_cache
from math import comb
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "paper"
SRC = PAPER / "journal_sources"
OUT = PAPER / "journals"


def _build_commit() -> str:
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "docs/paper", "scripts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return head + (" plus uncommitted changes" if dirty else "")


BUILD_COMMIT = _build_commit()

AUTHORS: list[dict[str, Any]] = [
    {
        "name": "Shaopei Ye",
        "aff": [1],
        "email": "shaopeiye55@gmail.com",
        "orcid": "0009-0006-3598-0469",
    },
    {
        "name": "Lan Wang",
        "aff": [2],
        "email": None,
        "orcid": None,
    },  # e-mail kept out of the repository
    {
        "name": "Peng Chen",
        "aff": [3],
        "email": "cpeng960@gmail.com",
        "orcid": "0009-0001-1105-6638",
    },
]
AFFILIATIONS = {
    1: "Faculty of Biology, Universitat de Barcelona, Barcelona, Spain",
    2: "Department of Otorhinolaryngology Head and Neck Surgery, Chengdu Fifth People's Hospital, Chengdu, Sichuan, China",
    3: "Department of Otorhinolaryngology, The Second People's Hospital of Meishan, No. 288 Dongpo Avenue South Section 4, Dongpo District, Meishan 620020, Sichuan Province, China",
}
CORRESPONDING = 2  # index into AUTHORS: Peng Chen
EQUAL_FIRST = (0, 1)  # Shaopei Ye and Lan Wang contributed equally (co-first authors)

JOURNALS: list[dict[str, str]] = [
    {
        "folder": "01_JMIR",
        "name": "Journal of Medical Internet Research",
        "short": "JMIR",
        "impact": "8.2 (2025 JIF, Journal Citation Reports 2026)",
        "apf": "US $3350",
        "site": "https://www.jmir.org",
        "why": (
            "The Journal of Medical Internet Research has published many evaluations of large language models in "
            "clinical tasks, and its readers include the clinicians and informaticians who would weigh whether such a "
            "system could support diagnosis. Our contribution is about how such systems should be evaluated, which we "
            "believe is of interest beyond rare diseases."
        ),
        "tier": "JMIR Publications 自家投稿系统；8.2 分；被拒时可同意转给 JMIR AI（6.1）或 JMIR Medical Informatics（5.0）继续审（JMIR 的转投机制，不用重新排版）",
    },
]

TITLE = (
    "Evaluating a Tool-Using Large Language Model Agent for Rare Disease Diagnosis With Masked Case "
    "Sources and External Patients: Prespecified Evaluation Study"
)
KEYWORDS = (
    "rare diseases; differential diagnosis; large language models; artificial intelligence; clinical decision "
    "support systems; Human Phenotype Ontology; data leakage; benchmarking; evaluation study"
)

# Results headings, shortened for an unnumbered layout.
HEADINGS = {
    "1. Introduction": "Introduction",
    "2. Methods": "Methods",
    "2.1 Task and scoring": "Task and Scoring",
    "2.2 Cases": "Cases",
    "2.3 Knowledge and masking": "Knowledge and Masking",
    "2.4 The agent": "The Agent",
    "2.5 Comparators": "Comparators",
    "2.6 Plans and records": "Plans and Records",
    "3. Results": "Results",
}
RESULT_HEADINGS = {
    "3.1": "Masking Halves a Published Tool's First-Place Accuracy",
    "3.2": "The First Version Led on Masked Held-Out Cases",
    "3.3": "The First Version Lost to Its Own Model on External Patients",
    "3.4": "Two Revisions Led Their Own Model in All Three Prespecified Tests",
    "3.5": "What the Lead Is Made Of",
    "3.6": "Comparison With a Frontier Model, and Cost",
}
CROSS_REFS = {
    "Section 2.4": "the Agent section",
    "Section 2.5": "the Comparators section",
    "Section 2.6": "the Plans and Records section",
    "Section 3.4": "the Results section on the three prespecified tests",
}
SPELLING = {
    "labelled": "labeled",
    "memorised": "memorized",
    "unfavourable": "unfavorable",
    "summarising": "summarizing",
    "summarises": "summarizes",
    "favours": "favors",
    "favourable": "favorable",
    "favour": "favor",
    "de-identified": "deidentified",
    "leukaemia": "leukemia",
    "hypertyrosinaemia": "hypertyrosinemia",
    "liquorice": "licorice",
    "tumours": "tumors",
    "Acknowledgements": "Acknowledgments",
}
ABBREVIATIONS = [
    ("AI", "artificial intelligence"),
    ("API", "application programming interface"),
    ("CI", "confidence interval"),
    ("HMS", "Hannover Medical School"),
    ("HPO", "Human Phenotype Ontology"),
    ("LIRICAL", "Likelihood Ratio Interpretation of Clinical Abnormalities"),
    ("LLM", "large language model"),
    ("OMIM", "Online Mendelian Inheritance in Man"),
    ("PEDIA", "Prioritization of Exome Data by Image Analysis"),
    ("PMC", "PubMed Central"),
]
FIRST_USE = {  # expanded where the body first uses them
    "OMIM": "Online Mendelian Inheritance in Man (OMIM)",
    "LIRICAL": "LIRICAL (Likelihood Ratio Interpretation of Clinical Abnormalities)",
    "PEDIA": "PEDIA (Prioritization of Exome Data by Image Analysis)",
}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
EXTRA_REFERENCES = [  # cited only in the JMIR end matter
    "rare-disease-agent: code, plans and per-case outcomes. GitHub. Accessed November 23, 2026. https://github.com/pipi0616/rare-disease-agent",
    "Luo W, Phung D, Tran T, et al. Guidelines for developing and reporting machine learning predictive models in biomedical research: a multidisciplinary view. J Med Internet Res. 2016;18(12):e323. doi:10.2196/jmir.5870",
]
FIGURES = [
    "fig1_design",
    "fig2_leakage",
    "fig3_heldout",
    "fig4_agent_vs_model",
    "fig5_new_tests",
    "fig6_by_findings",
]


# ---------------------------------------------------------------------------------------------
def sign_p(a: int, b: int) -> float:
    n = a + b
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(a, b) + 1)) / 2**n)


def jmir_p(p: float) -> str:
    """JMIR/AMA: P<.001; three decimals below .01; otherwise two decimals; P>.99 at the top."""
    if p < 0.001:
        return "*P*<.001"
    three = f"{p:.3f}"
    if float(three) < 0.01:
        return "*P*=" + three[1:]
    two = f"{p:.2f}"
    if float(two) >= 1.0:
        return "*P*>.99"
    return "*P*=" + two[1:]


P_TOKEN = re.compile(r"\bp ([=<]) ?([0-9.]+(?: × 10⁻[⁰¹²³⁴⁵⁶⁷⁸⁹]+)?)")
PAIR = re.compile(r"(\d+) : (\d+)")
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
UNPAIRED: list[str] = []


def convert_p(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        op, val = m.group(1), m.group(2)
        back = text[max(0, m.start() - 70) : m.start()]
        pairs = list(PAIR.finditer(back))
        if "×" in val:
            mant, exp = val.split(" × 10⁻")
            printed = float(mant) * 10 ** -int(exp.translate(SUP))
        else:
            printed = float(val)
        if pairs:  # the nearest paired count before the P value
            a, b = int(pairs[-1].group(1)), int(pairs[-1].group(2))
            exact = sign_p(a, b)
            consistent = (
                (exact < printed)
                if op == "<"
                else abs(exact - printed) <= max(0.006, 0.5 * printed)
            )
            if consistent:
                return jmir_p(exact)
        if op == "<" and printed == 0.001:
            return "*P*<.001"
        UNPAIRED.append(m.group(0) + "  …" + back[-50:])
        return jmir_p(printed) if op == "=" else "*P*<" + f"{printed:g}"[1:]

    return P_TOKEN.sub(repl, text)


def american(text: str) -> str:
    for uk, us in SPELLING.items():
        text = re.sub(rf"\b{uk}\b", us, text)
        text = re.sub(rf"\b{uk.capitalize()}\b", us.capitalize(), text)
    return text


def appendix_refs(text: str) -> str:
    text = re.sub(
        r"Supplementary sections (S\d+) and (S\d+)",
        r"sections \1 and \2 of Multimedia Appendix 1",
        text,
    )
    text = re.sub(r"Supplementary section (S\d+)", r"section \1 of Multimedia Appendix 1", text)
    text = re.sub(r"Supplementary Tables? (S\d+)", r"Table \1 in Multimedia Appendix 1", text)
    text = re.sub(r"Supplementary (S\d+)", r"Multimedia Appendix 1, section \1", text)
    text = text.replace("Supplementary material", "Multimedia Appendix 1")
    return text


# ---------------------------------------------------------------------------------------------
def _named(authors: str) -> int:
    return len([x for x in authors.split(",") if x.strip() and "et al" not in x])


def references() -> list[str]:
    """AMA style: all authors up to six, else the first three and et al. Full author lists come
    from the version of references.md before the lists were shortened (commit 0030222)."""
    current = (PAPER / "references.md").read_text().split("## To check by hand")[0]
    items = re.findall(r"^(\d+)\. (.+)$", current, flags=re.M)
    old = subprocess.run(
        ["git", "show", "0030222:docs/paper/references.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout
    full: dict[str, str] = {}
    for _, entry in re.findall(r"^(\d+)\. (.+)$", old.split("## To check by hand")[0], flags=re.M):
        authors, _, rest = entry.partition(". ")
        full[rest[:50]] = authors.replace("Jacobsen JO,", "Jacobsen JOB,")
    out = []
    for num, entry in items:
        authors, _, rest = entry.partition(". ")
        older = full.get(rest[:50])
        if older and "et al" not in older and _named(older) > _named(authors):
            authors = older
        authors = re.sub(r"\b([A-Z])-([A-Z])\b", r"\1\2", authors)  # initials without hyphens
        rest = re.sub(r"(?<=\d)–(?=[A-Z]?\d)", "-", rest)  # page ranges with hyphens
        rest = re.sub(
            r"arXiv:(\S+) \[preprint\]\. (\d{4})\.",
            r"arXiv. Preprint posted online \2. arXiv:\1",
            rest,
        )
        rest = rest.replace("as preprocessed in ref. ", "as preprocessed in reference ")
        rest = re.sub(r"\. (\d{4})\. p\. (\d+)[–-](\d+)\.", r". ACM; \1:\2-\3.", rest)
        out.append(f"{num}. {authors}. {rest}")
    for extra in EXTRA_REFERENCES:
        out.append(f"{len(out) + 1}. {extra}")
    return out


# ---------------------------------------------------------------------------------------------
def body_and_parts() -> tuple[str, dict[int, tuple[str, str]], dict[int, tuple[str, str, str]]]:
    s = (PAPER / "manuscript.md").read_text()
    body = s[s.index("## 1. Introduction") : s.index("## Declarations")]
    legends: dict[int, tuple[str, str]] = {}
    for m in re.finditer(
        r"^\*\*Fig\. (\d+)\. (.+?)\*\*(.*)$", s[s.index("## Figure legends") :], flags=re.M
    ):
        legends[int(m.group(1))] = (m.group(2).strip(), m.group(3).strip())
    tables: dict[int, tuple[str, str, str]] = {}
    tpart = s[s.index("## Tables") :]
    for m in re.finditer(r"\*\*Table (\d+)\. (.+?)\*\*(.*?)\n\n((?:\|.*\n?)+)", tpart):
        tables[int(m.group(1))] = (
            m.group(2).strip(),
            m.group(3).strip(),
            m.group(4).rstrip() + "\n",
        )
    return body, legends, tables


def restructure(body: str) -> str:
    # headings
    for old, new in HEADINGS.items():
        body = re.sub(rf"^(#+) {re.escape(old)}[ \t]*$", rf"\1 {new}", body, flags=re.M)
    for num, new in RESULT_HEADINGS.items():
        body = re.sub(rf"^### {re.escape(num)} .*$", f"### {new}", body, flags=re.M)
    # ethics, at the end of Methods
    ethics = (
        "### Ethical Considerations\n\n"
        "This study used only publicly available, deidentified data: published case reports and research datasets "
        "released for reuse. No patient was contacted, no clinical record was accessed, and no new data were "
        "collected from humans. The study involved no human participants and was not submitted for ethics review.\n\n"
    )
    body = body.replace("## Results\n", ethics + "## Results\n", 1)
    # discussion and conclusion into JMIR's subsections
    d0 = body.index("## 4. Discussion")
    c0 = body.index("## 5. Conclusion")
    disc, concl = body[d0:c0], body[c0:]
    paras = [p.strip() for p in disc.split("\n\n")[1:] if p.strip()]
    lead: dict[str, str] = {}
    for p in paras:
        m = re.match(r"\*\*(.+?)\*\*", p)
        lead[m.group(1) if m else ""] = p
    opening = lead[""]

    def pick(key: str) -> str:
        return next(p for k, p in lead.items() if k.startswith(key))

    limitations = re.sub(r"^\*\*Limitations\.\*\*\s*", "", pick("Limitations"))
    prior = (
        "Accuracies reported for language models and agents on published cases [7,10] are best read with these "
        "conditions in mind: how answers were judged, whether the system could search the web, and whether each "
        "case's source was masked. Our results suggest that, where the leakage pathway is not removed, it favors "
        "tools that read the annotations."
    )
    new = (
        "## Discussion\n\n### Principal Results\n\n"
        + opening
        + "\n\n"
        + pick("Tools and model")
        + "\n\n"
        + pick("Retrieving the right entry")
        + "\n\n"
        + pick("Memorisation")
        + "\n\n"
        + pick("Frontier models")
        + "\n\n"
        + "### Comparison With Prior Work\n\n"
        + pick("Benchmark leakage")
        + "\n\n"
        + pick("External tests")
        + "\n\n"
        + prior
        + "\n\n### Limitations\n\n"
        + limitations
        + "\n\n### Conclusions\n\n"
        + "\n\n".join(p.strip() for p in concl.split("\n\n")[1:] if p.strip())
        + "\n"
    )
    body = body[:d0] + new
    body = re.sub(r" \(3\.\d\)", "", body)  # the Results overview pointed to numbered sections
    for old, new_ref in CROSS_REFS.items():
        body = body.replace(old, new_ref)
    body = body.replace("Fig. ", "Figure ").replace("Figs. ", "Figures ")
    return body


def place_inline(
    body: str, legends: dict[int, tuple[str, str]], tables: dict[int, tuple[str, str, str]]
) -> str:
    paras = body.split("\n\n")
    after: dict[int, list[str]] = {}
    for n, (title, text) in legends.items():
        i = next(
            i
            for i, p in enumerate(paras)
            if re.search(rf"\bFigures? {n}[a-c]?\b", p) and not p.startswith("#")
        )
        cap = f"Figure {n}. {title} {text}".strip()
        after.setdefault(i, []).append(f"![{cap}](figures/{FIGURES[n - 1]}.png){{width=100%}}")
    for n, (title, note, table) in tables.items():
        i = next(
            i
            for i, p in enumerate(paras)
            if re.search(rf"\bTable {n}\b", p) and not p.startswith("#")
        )
        head = f"**Table {n}. {title}**" + (f" {note}" if note else "")
        after.setdefault(i, []).append(head + "\n\n" + table)
    out = []
    for i, p in enumerate(paras):
        out.append(p)
        out += after.get(i, [])
    return "\n\n".join(out)


def title_page() -> str:
    names = []
    for k, a in enumerate(AUTHORS):
        marks = (
            [str(x) for x in a["aff"]]
            + (["†"] if k in EQUAL_FIRST else [])
            + (["\\*"] if k == CORRESPONDING else [])
        )
        sup = ",".join(marks)
        names.append(f"{a['name']}^{sup}^")
    lines = [", ".join(names), ""]
    lines += [f"^{k}^ {v}" for k, v in AFFILIATIONS.items()] + [""]
    lines.append(
        "† "
        + " and ".join(AUTHORS[k]["name"] for k in EQUAL_FIRST)
        + " contributed equally to this work and are co-first authors."
    )
    lines.append("")
    c = AUTHORS[CORRESPONDING]
    lines.append(
        f"\\* Corresponding author: {c['name']}, {AFFILIATIONS[c['aff'][0]]}; email: {c['email']}"
    )
    lines.append("")
    lines.append(
        "ORCID: "
        + "; ".join(f"{a['name']}, https://orcid.org/{a['orcid']}" for a in AUTHORS if a["orcid"])
    )
    return "\n\n".join(x for x in lines if x is not None)


def end_matter(journal: dict[str, str]) -> str:
    refs = references()
    return f"""## Acknowledgments

The authors used a generative AI assistant (Claude, Anthropic) to write software, run the analyses and draft and edit the text, under their direction and with their review; the use is described in Multimedia Appendix 3. The authors take full responsibility for the content.

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## Conflicts of Interest

None declared.

## Data Availability

The code, the frozen case lists, the evaluation plans with their commit history, and per-case outcomes of most reported runs are available in the project repository [{len(refs) - 1}]. Every dataset used is public and pinned by version and checksum in the repository. The texts of the post-cutoff case reports are not redistributed, because some licenses are noncommercial; the repository lists each paper, the sentences kept and a checksum of the kept text, from which the set can be rebuilt.

## Authors' Contributions

Conceptualization: SY, PC. Methodology: SY. Software: SY. Formal analysis: SY. Investigation: LW (data collection), PC and LW (clinical interpretation). Data curation: SY, LW. Visualization: SY. Supervision: LW, PC. Writing – original draft: SY. Writing – review & editing: SY, LW, PC.

## Abbreviations

{chr(10).join(f"{a}: {b}" for a, b in ABBREVIATIONS)}

## Multimedia Appendix 1

Supplementary methods and results (sections S1–S13).

## Multimedia Appendix 2

Completed reporting checklist (Luo et al [{len(refs)}]).

## Multimedia Appendix 3

Use of generative AI in this work.

## References

{chr(10).join(refs)}
"""


def manuscript(journal: dict[str, str]) -> str:
    body, legends, tables = body_and_parts()
    body = restructure(body)
    body = place_inline(body, legends, tables)
    abstract = (SRC / "jmir_abstract.md").read_text().strip()
    text = (
        f'---\ntitle: "{TITLE}"\n---\n\n'
        + title_page()
        + "\n\n## Abstract\n\n"
        + abstract
        + f"\n\n**Keywords:** {KEYWORDS}\n\n"
        + body
        + "\n\n"
        + end_matter(journal)
    )
    text = appendix_refs(text)
    text = text.replace(
        "under the authors' direction (Multimedia Appendix 1, section S9).",
        "under the authors' direction (Multimedia Appendix 3).",
    )
    text = text.replace("p-values", "P values").replace("p-value", "P value")
    text = convert_p(text)
    text = first_use(text)
    return style(american(text))


def first_use(text: str) -> str:
    """Expand an abbreviation where the body (from the Introduction on) first uses it."""
    head, sep, body = text.partition("## Introduction")
    for abbr, full in FIRST_USE.items():
        m = re.search(rf"(?<![\w(]){abbr}(?![\w)])", body)
        if m:
            body = body[: m.start()] + full + body[m.end() :]
    return head + sep + body


def style(text: str) -> str:
    """AMA details: US dates, currency spacing."""
    text = re.sub(
        rf"\b(\d{{1,2}}) ({MONTHS}) and (\d{{1,2}}) ({MONTHS}) (\d{{4}})\b",
        r"\2 \1 and \4 \3, \5",
        text,
    )
    text = re.sub(rf"\b(\d{{1,2}}) ({MONTHS}) (\d{{4}})\b", r"\2 \1, \3", text)
    text = re.sub(rf"\b(\d{{1,2}}) ({MONTHS})\b", r"\2 \1", text)
    return text.replace("US$", "US $")


def supplement() -> str:
    t = (PAPER / "supplementary.md").read_text()
    t = re.sub(
        r'title: ".*?"',
        'title: "Multimedia Appendix 1. Supplementary methods and results"',
        t,
        count=1,
    )
    t = re.sub(r'subtitle: ".*?"', f'subtitle: "{TITLE}"', t, count=1)
    t = t.replace(" (Sections 3.4–3.5)", "").replace("Fig. ", "Figure ")
    t = t.replace("p-values", "P values").replace("Methods (Cases)", "the Cases section")
    t = t.replace("Section 2.4", "the Agent section").replace("Section 3.3", "the held-out results")
    t = t.replace("(p from 0.23 to 0.89)", "(*P* from .23 to .89)")
    t = convert_p(t)
    return style(american(t))


def cover_letter(journal: dict[str, str]) -> str:
    c = AUTHORS[CORRESPONDING]
    return f"""[Date]

To the Editor, {journal["name"]}

Dear Editor,

We submit for your consideration the Original Paper **"{TITLE}"**.

Language-model agents are now reported to name a rare disease from a patient's phenotype with striking accuracy. Three things make such reports hard to read: the public test cases are case reports that phenotype knowledge bases were curated from; a model may have memorized a public benchmark; and published cases are not patients as a clinic or a laboratory records them. Our manuscript evaluates an agent of this kind that we built, with these 3 problems in view, and reports what the measurement shows, with analyses that locate where the agent's lead comes from.

{journal["why"]}

What we believe is useful to your readers:

1. **The size of the leak, for everything an agent reads.** Hiding each test case's own source paper from everything the agent's tools read, similar patients included, halves the first-place accuracy of LIRICAL, a published and maintained tool, on 840 held-out published cases (63.2% to 30.1%), a fall of the size a recent preprint reported for the same tool on another sample of the same corpus.
2. **External tests catch what held-out tests miss.** The agent's first version passed its held-out test and then lost to its own model on a clinic's and a registry's patients; its traces showed a ranking blind to prevalence. Of 12 prespecified primary claims, 9 held and 3 failed, and all are reported.
3. **Three prespecified tests on cases never used in development.** Scored by identifier, two revisions of the agent (v1.1 on the patient sets, v2 on the case reports) ranked the confirmed disease first more often than their own model asked directly on 146 MyGene2 patients (52.1% vs 7.5%), 577 CADA cases (23.6% vs 14.7%) and 240 case reports published after the model's training cutoff (19.6% vs 8.8%). We report where the lead is not established: on the case reports when judged by disease name, and for the 205 patients of CADA's collaborators' cohorts; and GPT-6.1 asked directly on MyGene2 was not significantly different from the agent (54.8% vs 52.1%; a deficit of up to 12 points is not excluded).

The manuscript is original, has not been published, and is not under consideration elsewhere; it has not been posted as a preprint. It does not overlap with other published or submitted work by the authors. All authors have approved the manuscript and meet the criteria for authorship. Only public, deidentified data were used; the study involved no human participants and was not submitted for ethics review.

A generative AI assistant (Claude, Anthropic) was used to write software, run analyses and draft text under the authors' direction; this is declared in the Acknowledgments and described in Multimedia Appendix 3, and the authors take full responsibility for the content. A completed reporting checklist is provided as Multimedia Appendix 2.

We agree to pay the article processing fee ({journal["apf"]}) if the manuscript is accepted. We have read the journal's Fast-Track policy and do not request Fast Track. If the manuscript is not suitable for {journal["short"]}, we agree to its transfer to another JMIR Publications journal under the cascading peer-review policy.

Code, case lists, plans with their commit history and per-case outcomes are available in the project repository.

Thank you for your consideration.

Yours sincerely,

{c["name"]}\\
{AFFILIATIONS[c["aff"][0]]}\\
{c["email"]}; ORCID https://orcid.org/{c["orcid"]}\\
On behalf of all authors: {", ".join(a["name"] for a in AUTHORS)}
"""


def pandoc(md: Path, docx: Path, resource: Path) -> None:
    subprocess.run(
        [
            "pandoc",
            str(md),
            "-o",
            str(docx),
            "--from",
            "markdown",
            "--resource-path",
            str(resource),
        ],
        check=True,
    )


def write(journal: dict[str, str]) -> None:
    d = OUT / journal["folder"]
    if d.exists():
        shutil.rmtree(d)
    for sub in ("01_manuscript", "02_cover_letter", "03_figures", "04_multimedia_appendices"):
        (d / sub).mkdir(parents=True)
    # figures beside the manuscript source so pandoc can embed them, and as separate files
    (d / "01_manuscript" / "figures").mkdir()
    for k, f in enumerate(FIGURES, 1):
        for ext in ("png", "pdf"):
            shutil.copy(PAPER / "figures" / f"{f}.{ext}", d / "03_figures" / f"Figure_{k}.{ext}")
        shutil.copy(PAPER / "figures" / f"{f}.png", d / "01_manuscript" / "figures" / f"{f}.png")
    ms = d / "01_manuscript" / "manuscript.md"
    ms.write_text(manuscript(journal))
    pandoc(ms, d / "01_manuscript" / "manuscript.docx", d / "01_manuscript")
    shutil.rmtree(d / "01_manuscript" / "figures")
    ms.rename(d / "01_manuscript" / "manuscript_source.md")
    for name, text in (
        ("Multimedia_Appendix_1_supplementary", supplement()),
        (
            "Multimedia_Appendix_2_reporting_checklist",
            american((SRC / "reporting_checklist.md").read_text()),
        ),
        ("Multimedia_Appendix_3_generative_AI_use", (SRC / "ai_use_appendix.md").read_text()),
    ):
        p = d / "04_multimedia_appendices" / f"{name}.md"
        p.write_text(text)
        pandoc(p, p.with_suffix(".docx"), PAPER)
        p.unlink()
    cl = d / "02_cover_letter" / "cover_letter.md"
    cl.write_text(cover_letter(journal))
    pandoc(cl, cl.with_suffix(".docx"), PAPER)
    (d / "README.md").write_text(readme(journal))
    (d / "BEFORE_SUBMISSION.md").write_text(checklist(journal))
    lines: list[str] = []
    for path in sorted(q for q in d.rglob("*") if q.is_file() and q.name != "CHECKSUMS.sha256"):
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(d)}")
    (d / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n")


def readme(j: dict[str, str]) -> str:
    return f"""# {j["name"]} — submission package

- Journal: {j["name"]} ({j["site"]}); Impact Factor {j["impact"]}
- Article type: Original Paper
- Article processing fee: {j["apf"]}, payable on acceptance
- Built by `scripts/build_journals.py` from `docs/paper/` (from commit {BUILD_COMMIT}); do not edit the .docx by hand — change the sources and rebuild.

| folder | file | what it is |
|---|---|---|
| 01_manuscript | manuscript.docx | the manuscript in JMIR format: title page, structured abstract, keywords, IMRD sections, figures and tables inline, end matter, AMA references |
| 01_manuscript | manuscript_source.md | the Markdown the .docx was built from |
| 02_cover_letter | cover_letter.docx / .md | cover letter |
| 03_figures | Figure_1–6 .png (300 dpi) and .pdf (vector) | figures as separate files |
| 04_multimedia_appendices | Multimedia_Appendix_1_supplementary.docx | supplementary methods and results (S1–S13) |
| 04_multimedia_appendices | Multimedia_Appendix_2_reporting_checklist.docx | completed reporting checklist (Luo et al, 2016) |
| 04_multimedia_appendices | Multimedia_Appendix_3_generative_AI_use.docx | use of generative AI |
| . | BEFORE_SUBMISSION.md | what to check and enter before submitting (Chinese) |
| . | CHECKSUMS.sha256 | checksums of every file |
"""


def checklist(j: dict[str, str]) -> str:
    return f"""# 投稿前要做的事 — {j["name"]}

定位：{j["tier"]}
影响因子：{j["impact"]}；文章处理费：{j["apf"]}（录用后才付）
投稿网址：{j["site"]}（注册作者账号后，在个人主页里提交）

## 一、必须由你确认的内容（稿子里已按默认写好，不对就告诉我改）

1. **作者**（2026-11-23 按你的要求）：Shaopei Ye、Lan Wang 共同第一作者（叶排第一），Peng Chen 通讯作者。投稿时在系统里把陈鹏设为 corresponding author，期刊来信会发到他的邮箱 cpeng960@gmail.com；可以由你代投，但要和他说好。
2. **作者贡献**（2026-11-26 按你的要求）：王兰加了数据收集（Investigation: data collection；Data curation）。三位再确认一遍全文。
3. **单位**：叶：Faculty of Biology, Universitat de Barcelona；王兰：成都市第五人民医院耳鼻咽喉头颈外科；陈鹏：眉山市第二人民医院耳鼻喉科（都照上一篇写的）。
4. **王兰的 ORCID**：JMIR 要求所有作者在录用时都有 ORCID。王兰还没有，要她在 orcid.org 免费注册一个。
5. **作者贡献（CRediT）全文**：稿子里是参照上一篇写的初稿，请三位确认。
6. **基金**：写的是"没有专门资助"。有的话告诉我。
7. **利益冲突**：写的是"无"。
8. **伦理**：写的是"只用公开、去标识的数据，没有申请伦理审查"。如果两家医院的作者单位要求出具豁免说明，告诉我。
9. **投稿信里的两句声明**："没有发过预印本""和作者已发表或在投的其他论文没有重叠"（HEARS-LM 是另一个题目）。不对就告诉我。

10. **报告清单（JMIR AI 尤其相关）**：附件 2 填的是 Luo 等 2016 年的机器学习预测模型报告规范。JMIR AI 的须知推荐的是另一份：Klement 和 El Emam 2023 年的《Consolidated Reporting Guidelines for Prognostic and Diagnostic Machine Learning Modeling Studies》（JMIR 2023;25:e48763），它的清单在那篇文章的附件文件里，需要下载。你同意的话，我下载下来按它补填一份。

## 二、投稿前必须完成的

1. **把代码仓库推送到 GitHub 并公开**（稿子里写了仓库地址和"方案提交记录可查"）。要推送的包括分支 `feat/casereport-exam` 和本机标签 `plan/*`、`v1.0`。要我推送就说一声。
2. **生成式 AI 声明**：投稿系统里有一道专门的 AI 使用问题，按 Multimedia Appendix 3 的内容回答。JMIR 的规定是"建议/要求"把与 AI 的对话记录作为附件；这次的对话量很大，附件里写了"可应编辑要求提供"。编辑如果要，我可以把会话记录整理导出。
3. **推荐审稿人**（可选）：可以从参考文献作者里挑与你们没有合作关系的人，例如 PhEval 的作者（Jacobsen JOB，伦敦玛丽女王大学）、RareBench 的作者（Chen T，清华大学）、Phen2Disease 的作者（Zhu S，复旦大学）。邮箱要从他们最近论文的通讯信息里查。
4. 投稿信里的 [Date] 改成投稿当天日期。

## 三、投稿系统里要填/上传的

- 标题、摘要、关键词：从 manuscript.docx 复制
- 文章类型：Original Paper
- 上传：manuscript.docx；cover_letter.docx；03_figures 里的 6 张图（系统要求单独上传时）；04_multimedia_appendices 里的 3 个附件
- 是否同意被拒后转投 JMIR 其他期刊：投稿信里写的是"同意"
- 是否选 Fast Track：投稿信里写的是"不选"

## 四、已知的限制（审稿人可能会问）

- 影响因子来自 JMIR Publications 2026 年 6 月 18 日的官方公告（JCR 2026）。
- 正文约 4,550 词；JMIR 原创论文没有查到硬性字数上限。
"""


# =============================================================================================
# Journal of Medical Systems (Springer Nature) and BMJ Health & Care Informatics (BMJ)
# =============================================================================================
SHORT_TITLE = (
    "Masking case sources and testing on external patients: a prespecified evaluation of a tool-using "
    "large language model agent for rare disease diagnosis"
)
REPO_URL = "https://github.com/pipi0616/rare-disease-agent"
FIG_PLAIN = OUT / "_figures_plain"  # the same figures with p values written as in the text


def make_plain_figures() -> None:
    """Redraw the figures with p values as the Springer and BMJ texts write them (p = 0.065)."""
    import os

    if FIG_PLAIN.exists():
        shutil.rmtree(FIG_PLAIN)
    env = dict(os.environ, FIG_P_STYLE="plain", FIG_OUT=str(FIG_PLAIN))
    subprocess.run(
        [
            "uv",
            "run",
            "--offline",
            "--no-sync",
            "--with",
            "matplotlib==3.11.2",
            "python",
            "scripts/make_figures.py",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        timeout=600,
    )


TRIPOD_REF = (
    "Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated guidance for reporting clinical "
    "prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. "
    "doi:10.1136/bmj-2023-078378"
)
TRIPOD_AUTHORS_FULL = "Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, et al"
# placeholder keys in joms_body.md / bmj_body.md, with their number in manuscript.md
ITEM_MASTER = {
    "T:sets": 1,
    "T:heldout": 2,
    "T:tests": 3,
    "T:cada": 4,
    "T:idkind": 5,
    "F:design": 1,
    "F:mask": 2,
    "F:heldout": 3,
    "F:agentmodel": 4,
    "F:newtests": 5,
    "F:findings": 6,
}
MASTER_T = {n: k for k, n in ITEM_MASTER.items() if k.startswith("T")}
MASTER_F = {n: k for k, n in ITEM_MASTER.items() if k.startswith("F")}
DATA_AVAILABILITY = (
    "The code, the frozen case lists, the evaluation plans with their commit history, and per-case outcomes of "
    f"most reported runs are available in the project repository ({REPO_URL}). Every dataset used is public and "
    "pinned by version and checksum in the repository. The texts of the post-cutoff case reports are not "
    "redistributed, because some licences are non-commercial; the repository lists each paper, the sentences "
    "kept and a checksum of the kept text, from which the set can be rebuilt."
)
CREDIT = (
    "Conceptualization: SY, PC. Methodology: SY. Software: SY. Formal analysis: SY. Investigation: LW (data "
    "collection), PC and LW (clinical interpretation). Data curation: SY, LW. Visualization: SY. Supervision: LW, "
    "PC. Writing – original draft: SY. Writing – review & editing: SY, LW, PC."
)
ETHICS = (
    "Not applicable. This study used only publicly available, de-identified data: published case reports and "
    "research datasets released for reuse. No patient was contacted, no clinical record was accessed, and no new "
    "data were collected from humans; the study was not submitted for ethics review."
)

OTHER: list[dict[str, Any]] = [
    {
        "key": "joms",
        "folder": "02_Journal_of_Medical_Systems",
        "name": "Journal of Medical Systems",
        "publisher": "Springer Nature",
        "impact": "8.8 (2025 Journal Impact Factor; 5-year 6.0), as shown on the journal's Springer Nature page on 24 November 2026",
        "site": "https://link.springer.com/journal/10916",
        "title": SHORT_TITLE,
        "body": "joms_body.md",
        "abstract": "joms_abstract.md",
        "keywords": "Rare diseases; Differential diagnosis; Large language models; Clinical decision support; Data leakage; Benchmarking",
        "word_limit": 4000,
        "abstract_limit": 250,
        # all tables; the figures that repeat a table's numbers go to Online Resource 1, S14
        "main": {
            "T:sets",
            "T:heldout",
            "T:tests",
            "T:cada",
            "T:idkind",
            "F:design",
            "F:mask",
            "F:agentmodel",
        },
        "fig": "Fig. {n}",
        "tab": "Table {n}",
        "figs_plural": "Figs. {a} and {b}",
        "tabs_plural": "Tables {a} and {b}",
        "sfig": "Online Resource 1, Fig. {n}",
        "stab": "Online Resource 1, Table {n}",
        "supp": "Online Resource {n}",
        "supp_sec": "Online Resource 1, {s}",
        "supp_secs": "Online Resource 1, sections {a} and {b}",
        "supp_table": "Online Resource 1, Table {s}",
        "decl": "Statements and Declarations",
    },
    {
        "key": "bmj",
        "folder": "03_BMJ_Health_and_Care_Informatics",
        "name": "BMJ Health & Care Informatics",
        "publisher": "BMJ",
        "impact": "6.2 (Impact Factor; CiteScore 6.6; acceptance rate 24%; median 90 days to first decision with review), as shown on the journal's pages on 24 November 2026",
        "site": "https://informatics.bmj.com",
        "title": (
            "Masking case sources and testing on external patients: a prespecified retrospective "
            "evaluation of a tool-using large language model agent for rare disease diagnosis"
        ),
        "body": "bmj_body.md",
        "abstract": "bmj_abstract.md",
        "keywords": "Rare Diseases; Diagnosis, Differential; Artificial Intelligence; Decision Support Systems, Clinical; Benchmarking",
        "word_limit": 3000,
        "abstract_limit": 250,
        "main": {"T:sets", "F:design", "F:mask", "F:agentmodel", "T:tests"},  # at most five
        "fig": "figure {n}",
        "tab": "table {n}",
        "figs_plural": "figures {a} and {b}",
        "tabs_plural": "tables {a} and {b}",
        "sfig": "online supplemental figure {n}",
        "stab": "online supplemental table {n}",
        "supp": "online supplemental file {n}",
        "supp_sec": "online supplemental file 1, {s}",
        "supp_secs": "online supplemental file 1, sections {a} and {b}",
        "supp_table": "table {s} in online supplemental file 1",
        "decl": "the statements after the main text",
    },
]


def ai_use_paragraph(fmt: dict[str, Any]) -> str:
    ref = fmt["supp"].format(n=3)
    if fmt["key"] == "joms":
        return (
            "An AI assistant (Claude, Anthropic: Claude Fable 5.1 and 5.2 and Claude Opus 5.5, used through the "
            "Claude Code command-line tool with default settings between October and November 2026) wrote most of "
            "the software, ran the analyses and drafted the plans and the text under the authors' direction; "
            "separate sessions checked the manuscript's numbers against the per-case outcome files by script. "
            "It worked interactively rather than from fixed prompts; the authors approved each plan before its "
            f"test and reviewed the code, results and text ({ref}, with representative instructions)."
        )
    return (
        "An AI assistant (Claude Fable 5.1 and 5.2 and Claude Opus 5.5, Anthropic, via Claude Code, "
        "October–November 2026) wrote most of the software, ran "
        "the analyses and drafted the text under the authors' direction; the authors approved each plan and "
        f"reviewed all output ({ref})."
    )


def item_labels(fmt: dict[str, Any], body: str) -> tuple[dict[str, str], list[str]]:
    """Label each figure and table by order of first citation; items not in the journal's main
    text become supplementary figures and tables A, B, C."""
    order: list[str] = []
    for m in re.finditer(r"\[\[([TF]:\w+)\]\]", body):
        if m.group(1) not in order:
            order.append(m.group(1))
    assert set(order) == set(ITEM_MASTER), set(ITEM_MASTER) ^ set(order)
    lab: dict[str, str] = {}
    count = {"T": 0, "F": 0, "sT": 0, "sF": 0}
    for key in order:
        kind = key[0]
        if fmt["main"] is None or key in fmt["main"]:
            count[kind] += 1
            lab[key] = (fmt["fig"] if kind == "F" else fmt["tab"]).format(n=count[kind])
        else:
            count["s" + kind] += 1
            letter = "ABCDEF"[count["s" + kind] - 1]
            lab[key] = (fmt["sfig"] if kind == "F" else fmt["stab"]).format(n=letter)
    return lab, order


def _capitalise_starts(text: str) -> str:
    """A label that opens a sentence starts with a capital ("Table 1 lists ...")."""
    return re.sub(
        r"(^|\n\n|[.:] )(table|figure|online supplemental)\b",
        lambda m: m.group(1) + m.group(2)[0].upper() + m.group(2)[1:],
        text,
    )


def render_items(body: str, lab: dict[str, str]) -> str:
    body = re.sub(r"\[\[([TF]:\w+)\]\]", lambda m: lab[m.group(1)], body)
    return _capitalise_starts(body)


def xref(text: str, lab: dict[str, str], fmt: dict[str, Any]) -> str:
    """Rewrite references in manuscript.md's numbering (legends, table notes, supplement)."""

    def t(n: str) -> str:
        return lab[MASTER_T[int(n)]]

    def f(n: str) -> str:
        return lab[MASTER_F[int(n)]]

    def pair(a: str, b: str, plural: str) -> str:
        same = a.split()[:-1] == b.split()[:-1]
        if same:
            return plural.format(a=a.split()[-1], b=b.split()[-1])
        return f"{a} and {b}"

    text = re.sub(
        r"\bTables (\d) and (\d) and Supplementary Table (S\d+)",
        lambda m: (
            f"{t(m[2])}, {t(m[1])} and " + fmt["supp_table"].format(s=m[3])
            if t(m[1]).split()[0] != t(m[2]).split()[0]
            else m.group(0)
        ),
        text,
    )
    text = re.sub(
        r"\bTables (\d) and (\d)\b", lambda m: pair(t(m[1]), t(m[2]), fmt["tabs_plural"]), text
    )
    text = re.sub(r"\bTable (\d)\b", lambda m: t(m[1]), text)
    text = re.sub(r"\bFig\. (\d)([a-c]?)\b", lambda m: f(m[1]) + m[2], text)
    text = re.sub(
        r"Supplementary sections (S\d+) and (S\d+)",
        lambda m: fmt["supp_secs"].format(a=m[1], b=m[2]),
        text,
    )
    text = re.sub(
        r"Supplementary [Tt]ables? (S\d+)", lambda m: fmt["supp_table"].format(s=m[1]), text
    )
    text = re.sub(
        r"Supplementary (?:section )?(S\d+)", lambda m: fmt["supp_sec"].format(s=m[1]), text
    )
    text = text.replace("Section 2.5", "Comparators").replace("Section 2.4", "The agent")
    return _capitalise_starts(text)


# --- citations -------------------------------------------------------------------------------
CITE = re.compile(r"\[(\d+(?:\s*[–,-]\s*\d+)*)\]")


def _expand(s: str) -> list[int]:
    out: list[int] = []
    for part in re.split(r"\s*,\s*", s):
        if re.search(r"[–-]", part):
            a, b = re.split(r"\s*[–-]\s*", part)
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def _compress(nums: list[int]) -> str:
    nums = sorted(set(nums))
    runs: list[list[int]] = []
    for n in nums:
        if runs and n == runs[-1][-1] + 1:
            runs[-1].append(n)
        else:
            runs.append([n])
    parts = []
    for r in runs:
        if len(r) >= 3:
            parts.append(f"{r[0]}-{r[-1]}")
        else:
            parts += [str(x) for x in r]
    return "[" + ", ".join(parts) + "]"


def citation_order(texts: list[str]) -> dict[int, int]:
    order: list[int] = []
    for text in texts:
        for m in CITE.finditer(text):
            for n in _expand(m.group(1)):
                if n not in order:
                    order.append(n)
    return {old: new for new, old in enumerate(order, 1)}


def renumber(text: str, mapping: dict[int, int]) -> str:
    return CITE.sub(lambda m: _compress([mapping[n] for n in _expand(m.group(1))]), text)


# --- references ------------------------------------------------------------------------------
REF_RE = re.compile(
    r"^(?P<au>.+?)\. (?P<ti>.+?[.?!]) (?P<jo>[^.?]+?)\. (?P<yr>\d{4});(?P<vol>[^:]+):(?P<pg>[^ ]+?)\.(?: doi:(?P<doi>\S+))?$"
)
ARXIV_RE = re.compile(
    r"^(?P<au>.+?)\. (?P<ti>.+?[.?]) arXiv:(?P<id>\S+) \[preprint\]\. (?P<yr>\d{4})\.$"
)


def master_references() -> dict[int, str]:
    current = (PAPER / "references.md").read_text().split("## To check by hand")[0]
    refs = {int(n): e for n, e in re.findall(r"^(\d+)\. (.+)$", current, flags=re.M)}
    assert 31 not in refs, "references.md has grown: move TRIPOD_REF to a free number"
    refs[31] = TRIPOD_REF  # cited as [31] in joms_body.md and bmj_body.md
    return refs


@lru_cache(maxsize=1)
def _fuller_authors() -> dict[str, str]:
    old = subprocess.run(
        ["git", "show", "0030222:docs/paper/references.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout
    full: dict[str, str] = {}
    for _, entry in re.findall(r"^(\d+)\. (.+)$", old.split("## To check by hand")[0], flags=re.M):
        authors, _, rest = entry.partition(". ")
        full[rest[:50]] = authors.replace("Jacobsen JO,", "Jacobsen JOB,")
    return full


def format_reference(num: int, entry: str, style: str, mapping: dict[int, int]) -> str:
    """style 'springer' (Springer basic) or 'bmj' (BMJ Vancouver: first three authors, et al)."""
    authors, _, rest = entry.partition(". ")
    if style == "springer":
        older = _fuller_authors().get(rest[:50])
        if num == 31:
            older = TRIPOD_AUTHORS_FULL
        if rest.startswith("Auditing evaluation artifacts"):  # arXiv 2610.33592, 2026-11-25
            older = "Yang J, Liu P, Li X, Li S, Cao Y, Feng Y, Li H"
        if rest.startswith(
            "Towards a standard benchmark for phenotype-driven"
        ):  # Crossref, 2026-11-25
            older = "Bridges Y, de Souza V, Cortes KG, Haendel M, Harris NL, Korn DR, et al"
        if older and _named(older) > _named(authors):
            authors = older
        authors = re.sub(r",? et al\.?$", " et al", authors)
    if entry.startswith("MyGene2."):
        text = re.sub(
            r"as preprocessed in ref\. (\d+)",
            lambda m: f"as preprocessed in reference {mapping[int(m.group(1))]}",
            entry,
        )
        if style == "springer":
            text = text.replace("doi:", "https://doi.org/").rstrip(".")
        return text
    m = REF_RE.match(entry)
    a = ARXIV_RE.match(entry)
    if entry.split(". ", 1)[1].startswith("RareBench"):
        title = "RareBench: can LLMs serve as rare diseases specialists?"
        proc = "In: Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining"
        doi = "10.1145/3637528.3671576"
        assert title in entry and proc in entry and doi in entry and "4850–4861" in entry
        if style == "springer":
            return f"{authors} (2024) {title} {proc}. ACM, New York, pp 4850–4861. https://doi.org/{doi}"
        return f"{authors}. {title} {proc}. 2024:4850–4861. doi:{doi}"
    if a:
        arx = a["id"]
        if style == "springer":
            ti = a["ti"] if a["ti"].endswith("?") else a["ti"][:-1] + "."
            return f"{authors} ({a['yr']}) {ti} arXiv:{arx}. https://doi.org/10.48550/arXiv.{arx}"
        return f"{authors}. {a['ti']} arXiv {arx} [Preprint]. {a['yr']}. doi:10.48550/arXiv.{arx}"
    assert m, f"reference {num} not parsed: {entry}"
    title = m["ti"]
    if style == "springer":
        title = title[:-1] if title.endswith(".") else title
        sep = " " if title.endswith(("?", "!")) else ". "
        out = f"{authors} ({m['yr']}) {title}{sep}{m['jo']} {m['vol']}:{m['pg']}"
        return out + (f". https://doi.org/{m['doi']}" if m["doi"] else "")
    out = f"{authors}. {title} {m['jo']} {m['yr']};{m['vol']}:{m['pg']}."
    return out + (f" doi:{m['doi']}" if m["doi"] else "")


def reference_list(style: str, mapping: dict[int, int]) -> list[str]:
    refs = master_references()
    inverse = {new: old for old, new in mapping.items()}
    return [
        f"{new}. {format_reference(inverse[new], refs[inverse[new]], style, mapping)}"
        for new in sorted(inverse)
    ]


# --- checks ----------------------------------------------------------------------------------
NUM_TOKEN = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?")
PAIR_TOKEN = re.compile(r"\d+ : \d+")


def source_numbers() -> tuple[set[str], set[str]]:
    src = (PAPER / "manuscript.md").read_text() + (PAPER / "supplementary.md").read_text()
    return set(NUM_TOKEN.findall(src)), set(PAIR_TOKEN.findall(src))


def check_numbers(name: str, text: str, allowed: set[str] = frozenset()) -> list[str]:  # type: ignore[assignment]
    nums, pairs = source_numbers()
    text = re.sub(r"\[\[[TF]:\w+\]\]|\[\d+(?:\s*[–,-]\s*\d+)*\]", " ", text)
    bad = [
        f"{name}: number {x}"
        for x in NUM_TOKEN.findall(text)
        if x.rstrip(",") not in nums | allowed
    ]
    bad += [f"{name}: pair {x}" for x in PAIR_TOKEN.findall(text) if x not in pairs]
    return bad


def check_p(name: str, text: str) -> list[str]:
    """Each p value next to a paired count must match the exact two-sided sign test."""
    bad = []
    for m in re.finditer(r"\bp ([=<]) ([0-9.]+(?: × 10⁻[⁰¹²³⁴⁵⁶⁷⁸⁹]+)?)", text):
        back = text[max(0, m.start() - 70) : m.start()]
        pairs = list(PAIR.finditer(back))
        if not pairs:
            continue
        exact = sign_p(int(pairs[-1].group(1)), int(pairs[-1].group(2)))
        op, val = m.group(1), m.group(2)
        if "×" in val:
            mant, exp = val.split(" × 10⁻")
            printed = float(mant) * 10 ** -int(exp.translate(SUP))
            ok = abs(exact - printed) <= 0.5 * printed
        elif op == "<":
            ok = exact < float(val)
        else:
            decimals = len(val.split(".")[1])
            ok = abs(exact - float(val)) <= 0.5 * 10**-decimals + 1e-12
        if not ok:
            bad.append(
                f"{name}: {m.group(0)} but sign test of {pairs[-1].group(0)} gives {exact:.4g}"
            )
    return bad


def check_figure_p(name: str, txt: str) -> list[str]:
    """Pairs and p values in a figure: 'a : b' then 'p = x' on the next line, same column."""
    bad: list[str] = []
    lines = txt.split("\n")
    for i, line in enumerate(lines[:-1]):
        for m in PAIR.finditer(line):
            same = line[m.end() : m.end() + 16]
            below = lines[i + 1][max(0, m.start() - 4) : m.end() + 12]
            pm = re.match(r",? ?p ([=<]) ([0-9.]+)", same) or re.search(
                r"p ([=<]) ([0-9.]+)", below
            )
            if not pm:
                bad.append(f"figure {name}: no p value under {m.group(0)}")
                continue
            bad += check_p(f"figure {name}", f"{m.group(0)}, {pm.group(0)}")
    return bad


def words(text: str) -> int:
    return len(re.findall(r"\S+", text))


# --- documents -------------------------------------------------------------------------------
def legends_and_tables(
    fmt: dict[str, Any], lab: dict[str, str]
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Captions and tables keyed by placeholder, in the journal's labels and style."""
    _, legends, tables = body_and_parts()
    caps: dict[str, str] = {}
    files: dict[str, str] = {}
    tabs: dict[str, str] = {}
    for n, (title, text) in legends.items():
        key = MASTER_F[n]
        text = xref(text, lab, fmt)
        if fmt["key"] == "joms":  # Springer: "Fig. 1" in bold, no punctuation at the end
            caps[key] = f"**{lab[key]}** {title} {text}".strip().rstrip(".")
        else:
            caps[key] = f"**{lab[key][0].upper() + lab[key][1:]}** {title} {text}".strip()
        files[key] = FIGURES[n - 1]
    for n, (title, note, table) in tables.items():
        key = MASTER_T[n]
        head = f"**{lab[key][0].upper() + lab[key][1:]}** {title}" + (
            f" {xref(note, lab, fmt)}" if note else ""
        )
        tabs[key] = head + "\n\n" + xref(table, lab, fmt)
    return caps, files, tabs


def place_items(body: str, fmt: dict[str, Any], lab: dict[str, str], order: list[str]) -> str:
    """Tables after the paragraph that first cites them; figures too for Springer (inline), but
    for BMJ only the legends, at the end of the manuscript."""
    caps, files, tabs = legends_and_tables(fmt, lab)
    paras = body.split("\n\n")
    after: dict[int, list[str]] = {}
    for key in order:
        if fmt["main"] is not None and key not in fmt["main"]:
            continue
        i = next(i for i, p in enumerate(paras) if f"[[{key}]]" in p and not p.startswith("#"))
        if key.startswith("T"):
            after.setdefault(i, []).append(tabs[key])
        elif fmt["key"] == "joms":
            after.setdefault(i, []).append(
                f"![{caps[key]}](figures/{files[key]}.png){{width=100%}}"
            )
    out = []
    for i, p in enumerate(paras):
        out.append(p)
        out += after.get(i, [])
    return "\n\n".join(out)


def header_block(fmt: dict[str, Any]) -> str:
    c = AUTHORS[CORRESPONDING]
    return (
        f"**Article:** {fmt['title']}  \n**Journal:** {fmt['name']}  \n"
        f"**Authors:** {', '.join(a['name'] for a in AUTHORS)}  \n"
        f"**Corresponding author:** {c['name']}, {AFFILIATIONS[c['aff'][0]]}; {c['email']}  \n"
        "Reference numbers in square brackets refer to the main article's reference list.\n\n"
    )


def supplement_other(fmt: dict[str, Any], lab: dict[str, str], order: list[str]) -> str:
    t = (PAPER / "supplementary.md").read_text()
    s1 = fmt["supp"].format(n=1)
    s1 = s1[0].upper() + s1[1:]
    t = re.sub(r'title: ".*?"', f'title: "{s1}. Supplementary methods and results"', t, count=1)
    t = re.sub(r'subtitle: ".*?"', f'subtitle: "{fmt["title"]}"', t, count=1)
    head_end = t.index("---", 3) + 3
    t = t[:head_end] + "\n\n" + header_block(fmt) + t[head_end:].lstrip("\n")
    t = t.replace(" (Sections 3.4–3.5)", "").replace("Methods (Cases)", "Methods, Cases")
    t = t.replace("Section 2.4", "the Methods (The agent)").replace(
        "Section 3.3", "the held-out results"
    )
    t = t.replace(
        "Table 2's nearest-patients row", f"the nearest-patients row of {lab['T:heldout']}"
    )
    t = xref(t, lab, fmt)
    t = t.replace("P values", "p-values").replace("P value", "p-value")
    if fmt["main"] is not None:  # BMJ: the figures and tables that do not fit the main text
        caps, files, tabs = legends_and_tables(fmt, lab)
        moved = [k for k in order if k not in fmt["main"]]
        what = "Figures and tables" if any(k.startswith("T") for k in moved) else "Figures"
        where = (
            "online supplemental material" if fmt["key"] == "bmj" else "part of Online Resource 1"
        )
        parts = [f"## S14. {what} cited in the main text as {where}"]
        for key in order:
            if key in fmt["main"]:
                continue
            if key.startswith("F"):
                parts.append(caps[key])
                parts.append(f"![](figures/{files[key]}.png){{width=100%}}")
            else:
                parts.append(tabs[key])
        s14 = "\n\n".join(parts).replace(" in online supplemental file 1", "")
        s14 = s14.replace("online supplemental file 1, S", "S").replace("Online Resource 1, ", "")
        t = t.rstrip() + "\n\n" + s14 + "\n"
    return t


def title_page_other(fmt: dict[str, Any], word_count: int) -> str:
    tp = title_page()
    if fmt["key"] == "bmj":
        tp += f"\n\n**Word count:** {word_count} (main text, excluding title page, abstract, key messages, tables, figure legends, statements and references)"
        tp += f"\n\n**Keywords:** {fmt['keywords']}"
    return tp


def statements(fmt: dict[str, Any]) -> str:
    if fmt["key"] == "joms":
        return f"""## Statements and Declarations

**Funding** The authors declare that no funds, grants, or other support were received during the preparation of this manuscript.

**Competing interests** The authors have no relevant financial or non-financial interests to disclose.

**Ethics approval** {ETHICS}

**Consent to participate** Not applicable.

**Consent to publish** Not applicable.

**Data availability** {DATA_AVAILABILITY}

**Code availability** All code — the agent and its tools, the evaluation harness, the masking and leak audit, and the statistical and figure scripts — is in the project repository ({REPO_URL}).

**Author contributions** Shaopei Ye and Lan Wang contributed equally to this work and are co-first authors. {CREDIT}
"""
    s3 = fmt["supp"].format(n=3)
    orcid = "; ".join(f"{a['name']} https://orcid.org/{a['orcid']}" for a in AUTHORS if a["orcid"])
    return f"""## Statements

**Contributors** SY and LW contributed equally to this work and are co-first authors. {CREDIT} PC is the guarantor. An AI assistant (Claude, Anthropic) was used to write software, run the analyses and draft and edit the text under the authors' direction, as described in the Methods and {s3}; the authors reviewed its output and take full responsibility for the content.

**Funding** The authors have not declared a specific grant for this research from any funding agency in the public, commercial or not-for-profit sectors.

**Competing interests** None declared.

**Patient consent for publication** Not applicable.

**Ethics approval** {ETHICS}

**Provenance and peer review** Not commissioned; externally peer reviewed.

**Data availability statement** Data are available in a public, open access repository. {DATA_AVAILABILITY}

**ORCID iDs** {orcid}
"""


def manuscript_other(fmt: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Returns the manuscript, the supplement and facts for the checks and the README."""
    raw = (SRC / fmt["body"]).read_text()
    raw = raw.replace("[[AI_USE]]", ai_use_paragraph(fmt))
    lab, order = item_labels(fmt, raw)
    body = place_items(raw, fmt, lab, order)
    body = render_items(body, lab)
    main_words = words(render_items(raw, lab))
    abstract = (SRC / fmt["abstract"]).read_text().strip()
    supp = supplement_other(fmt, lab, order)
    caps, _, _ = legends_and_tables(fmt, lab)
    legends_end = ""
    if fmt["key"] == "bmj":
        legends_end = "\n\n## Figure legends\n\n" + "\n\n".join(
            caps[k] for k in order if k.startswith("F") and k in fmt["main"]
        )
    mapping = citation_order([body + legends_end, supp])
    body, supp, legends_end = (renumber(x, mapping) for x in (body, supp, legends_end))
    style = "springer" if fmt["key"] == "joms" else "bmj"
    refs = reference_list(style, mapping)
    front = f'---\ntitle: "{fmt["title"]}"\n---\n\n' + title_page_other(fmt, main_words)
    front += "\n\n## Abstract\n\n" + abstract
    if fmt["key"] == "joms":
        front += f"\n\n**Keywords** {fmt['keywords']}"
    else:
        front += "\n\n## Key messages\n\n" + (SRC / "bmj_key_messages.md").read_text().strip()
    text = (
        front
        + "\n\n"
        + body
        + "\n\n"
        + statements(fmt)
        + "\n## References\n\n"
        + "\n".join(refs)
        + legends_end
        + "\n"
    )
    if fmt["key"] == "bmj":  # BMJ: first-level headings in capitals
        text = re.sub(r"^## (.+)$", lambda m: "## " + m.group(1).upper(), text, flags=re.M)
    facts = {
        "main_words": main_words,
        "abstract_words": words(abstract.replace("**", "")),
        "n_refs": len(refs),
        "labels": lab,
        "order": order,
        "mapping": mapping,
        "raw": raw,
        "abstract": abstract,
    }
    return text, supp, facts


def size_columns(md: str) -> str:
    """Pipe tables: column widths in proportion to their longest cell (pandoc reads the widths
    from the dashes of the separator row), so long text gets the room."""
    out: list[str] = []
    block: list[str] = []

    def flush() -> None:
        if len(block) >= 2 and re.match(r"^\|[-:| ]+\|$", block[1]):
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in block]
            ncol = len(rows[0])
            longest = [
                max(len(r[k]) for r in rows if k < len(r) and r is not rows[1]) for k in range(ncol)
            ]
            dashes = [max(14, min(60, n)) for n in longest]
            block[1] = "|" + "|".join("-" * d for d in dashes) + "|"
        out.extend(block)
        block.clear()

    for line in md.split("\n"):
        if line.startswith("|"):
            block.append(line)
        else:
            flush()
            out.append(line)
    flush()
    return "\n".join(out)


def docx_to_pdf(docx: Path, outdir: Path) -> Path:
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(docx)],
        check=True,
        capture_output=True,
    )
    return outdir / (docx.stem + ".pdf")


def md_to_pdf(md_text: str, pdf: Path, resource: Path) -> None:
    tmp = pdf.parent / ("_" + pdf.stem)
    tmp.mkdir()
    (tmp / "doc.md").write_text(md_text)
    pandoc(tmp / "doc.md", tmp / "doc.docx", resource)
    shutil.move(str(docx_to_pdf(tmp / "doc.docx", tmp)), pdf)
    shutil.rmtree(tmp)


def figure_files(fmt: dict[str, Any], lab: dict[str, str], dest: Path) -> list[str]:
    """Springer: EPS (vector) and 600-dpi TIFF named Fig1..; BMJ: PDF and 1200-dpi TIFF of the
    main-text figures, named Figure_1.."""
    made = []
    for key, n in sorted(
        ((k, v) for k, v in ITEM_MASTER.items() if k.startswith("F")), key=lambda kv: kv[1]
    ):
        if fmt["main"] is not None and key not in fmt["main"]:
            continue
        num = lab[key].split()[-1]
        src = FIG_PLAIN / f"{FIGURES[n - 1]}.pdf"
        stem = f"Fig{num}" if fmt["key"] == "joms" else f"Figure_{num}"
        if fmt["key"] == "joms":
            subprocess.run(["pdftops", "-eps", str(src), str(dest / f"{stem}.eps")], check=True)
        else:
            shutil.copy(src, dest / f"{stem}.pdf")
        subprocess.run(
            [
                "pdftoppm",
                "-r",
                "600" if fmt["key"] == "joms" else "1200",
                "-tiff",
                "-tiffcompression",
                "lzw",
                "-singlefile",
                str(src),
                str(dest / stem),
            ],
            check=True,
        )
        made.append(f"{stem} ← {FIGURES[n - 1]} ({lab[key]})")
    return made


def cover_letter_other(fmt: dict[str, Any], facts: dict[str, Any]) -> str:
    c = AUTHORS[CORRESPONDING]
    s2, s3 = fmt["supp"].format(n=2), fmt["supp"].format(n=3)
    if fmt["key"] == "joms":
        why = (
            "The Journal of Medical Systems gives priority to work on how health information systems are evaluated, "
            "and asks authors of clinical AI studies to report data provenance, splits with temporal or site "
            "separation, baseline comparators and a reproducibility plan. Our manuscript is built around these: "
            "each test case's known source paper is masked; the tests include patients from outside the "
            "development source and cases published after the model's training cutoff; and the code, plans and "
            "per-case outcomes are available."
        )
        kind = "Research article"
        extra = (
            f"The completed TRIPOD+AI checklist is uploaded as {s2}. Use of generative AI is described in the Methods "
            f"(tool, models, dates, access, human verification) and in {s3}."
        )
        fee = (
            "The study does not deploy the agent; it shows what evidence a health system should ask for before "
            "deploying one. The agent costs about one US cent and a median of 17 seconds per case on pinned public "
            "knowledge and records the evidence behind each candidate, so the same protocol can be applied to any "
            "comparable system. We do not request open access publication at this stage."
        )
    else:
        why = (
            "BMJ Health & Care Informatics publishes evaluations of informatics that supports health and care, and "
            "its readers include the clinicians and informaticians who would decide whether such decision support "
            "can be trusted. Our contribution is about how such systems should be evaluated, which we believe "
            "matters beyond rare diseases."
        )
        kind = "Original research"
        extra = (
            f"The completed TRIPOD+AI checklist is provided as {s2}. In line with BMJ's policy on AI use, the use of "
            f"a generative AI assistant is acknowledged in the Contributors statement and described in the Methods "
            f"and in {s3}."
        )
        fee = (
            "We understand that the journal is open access and levies an article processing charge if the "
            "manuscript is accepted. If the manuscript is not suitable for the journal, we agree to its transfer to "
            "another BMJ journal."
        )
    return f"""[Date]

To the Editor, {fmt["name"]}

Dear Editor,

We submit for your consideration the {kind} **"{fmt["title"]}"** (main text {facts["main_words"]} words; abstract {facts["abstract_words"]} words).

Language-model agents are now reported to name a rare disease from a patient's phenotype with striking accuracy. Three things make such reports hard to read: the public test cases are case reports that phenotype knowledge bases were curated from; a model may have memorised a public benchmark; and published cases are not patients as a clinic or a laboratory records them. Our manuscript evaluates an agent of this kind that we built, with these three problems in view, and reports what the measurement shows, with analyses that locate where the agent's lead comes from.

{why}

What we believe is useful to your readers:

1. **The size of the leak, for everything an agent reads.** Hiding each test case's own source paper from everything the agent's tools read, similar patients included, halves the first-place accuracy of LIRICAL, a published and maintained tool, on 840 held-out published cases (63.2% to 30.1%), a fall of the size a recent preprint reported for the same tool on another sample of the same corpus.
2. **External tests catch what held-out tests miss.** The agent's first version passed its held-out test and then lost to its own model on a clinic's and a registry's patients; its traces showed a ranking blind to prevalence. Of twelve prespecified primary claims, nine held and three failed, and all are reported.
3. **Three prespecified tests on cases never used in development.** Scored by identifier, two revisions of the agent (v1.1 on the patient sets, v2 on the case reports) ranked the confirmed disease first more often than their own model asked directly on 146 MyGene2 patients (52.1% vs 7.5%), 577 CADA cases (23.6% vs 14.7%) and 240 case reports published after the model's training cutoff (19.6% vs 8.8%). We report where the lead is not established: on the case reports when judged by disease name, and for the 205 patients of CADA's collaborators' cohorts; and GPT-6.1 asked directly on MyGene2 was not significantly different from the agent (54.8% vs 52.1%; a deficit of up to 12 points is not excluded).

The manuscript is original, has not been published, and is not under consideration elsewhere; it has not been posted as a preprint. It does not overlap with other published or submitted work by the authors. All authors have approved the manuscript and meet the criteria for authorship. Only public, de-identified data were used; the study involved no human participants and was not submitted for ethics review.

{extra}

{fee}

Code, case lists, plans with their commit history and per-case outcomes are available in the project repository.

Thank you for your consideration.

Yours sincerely,

{c["name"]}\\
{AFFILIATIONS[c["aff"][0]]}\\
{c["email"]}; ORCID https://orcid.org/{c["orcid"]}\\
On behalf of all authors: {", ".join(a["name"] for a in AUTHORS)}
"""


def readme_other(fmt: dict[str, Any], facts: dict[str, Any], figs: list[str]) -> str:
    s = [fmt["supp"].format(n=k) for k in (1, 2, 3)]
    supp_dir = "04_online_resources" if fmt["key"] == "joms" else "04_supplementary"
    names = (
        ["ESM_1.pdf", "ESM_2.pdf", "ESM_3.pdf"]
        if fmt["key"] == "joms"
        else [
            "Supplementary_file_1.pdf",
            "Supplementary_file_2_TRIPOD-AI.pdf",
            "Supplementary_file_3_AI_use.pdf",
        ]
    )
    main_items = ", ".join(
        f"{facts['labels'][k]}" for k in facts["order"] if fmt["main"] is None or k in fmt["main"]
    )
    rows = "\n".join(f"| 03_figures | {f} | figure file |" for f in figs)
    return f"""# {fmt["name"]} — submission package

- Journal: {fmt["name"]} ({fmt["site"]}), {fmt["publisher"]}; Impact Factor {fmt["impact"]}
- Built by `scripts/build_journals.py` from `docs/paper/` (from commit {BUILD_COMMIT}); do not edit the .docx by hand — change the sources and rebuild.
- Main text {facts["main_words"]} words (limit {fmt["word_limit"]}); abstract {facts["abstract_words"]} words (limit {fmt["abstract_limit"]}); {facts["n_refs"]} references.
- Figures and tables in the main text: {main_items}.

| folder | file | what it is |
|---|---|---|
| 01_manuscript | manuscript.docx | the manuscript |
| 01_manuscript | manuscript_source.md | the Markdown the .docx was built from |
| 02_cover_letter | cover_letter.docx / .md | cover letter |
{rows}
| {supp_dir} | {names[0]} | {s[0]}: supplementary methods and results (S1–S13{", S14" if fmt["main"] else ""}) |
| {supp_dir} | {names[1]} | {s[1]}: completed TRIPOD+AI checklist |
| {supp_dir} | {names[2]} | {s[2]}: use of generative AI |
| . | BEFORE_SUBMISSION.md | what to check and enter before submitting (Chinese) |
| . | CHECKSUMS.sha256 | checksums of every file |
"""


def checklist_other(fmt: dict[str, Any], facts: dict[str, Any]) -> str:
    common = f"""1. **作者**：Shaopei Ye、Lan Wang 共同第一作者（叶排第一），Peng Chen 通讯作者。投稿时在系统里把陈鹏设为 corresponding author，期刊来信会发到 cpeng960@gmail.com。
2. **作者贡献**（2026-11-26 按你的要求）：王兰加了数据收集（Investigation: data collection；Data curation）。投稿时系统里也要按这个填。王兰的邮箱没有写进仓库（仓库是公开的），投稿系统要填作者邮箱时请手动填。
3. **王兰的 ORCID**：还没有，建议在 orcid.org 免费注册一个。
4. **基金**写"没有专门资助"，**利益冲突**写"无"，**伦理**写"只用公开、去标识的数据，没有申请伦理审查"。不对就告诉我。
5. **投稿信里的声明**："没有发过预印本""和作者其他论文没有重叠"。不对就告诉我。
6. **把代码仓库推送到 GitHub 并公开**：稿子里写了仓库地址 {REPO_URL}。要我推送就说一声（含本机标签 `plan/*`、`v1.0`）。
7. 投稿信里的 [Date] 改成投稿当天日期。
8. **一次只投一本**：三本不能同时投，被拒后再投下一本。"""
    if fmt["key"] == "joms":
        return f"""# 投稿前要做的事 — {fmt["name"]}

出版社：Springer Nature；投稿入口：期刊主页（{fmt["site"]}）的 Submit manuscript。
影响因子：{fmt["impact"]}。期刊页面写的是：投稿到第一次决定中位 8 天，投稿到录用中位 76 天。
文章类型：Research（正文 ≤ 4,000 词、摘要 ≤ 300 词；Springer 通用要求摘要 150–250 词）。现在正文 {facts["main_words"]} 词、摘要 {facts["abstract_words"]} 词、参考文献 {facts["n_refs"]} 条。
费用：订阅期刊，不选开放获取就不用付版面费（选 Open Choice 才收费）。

## 一、要你确认的

{common}
9. **作者贡献和利益冲突要在投稿系统里再填一遍**：期刊写明"只用系统里填的内容"，按稿子末尾 Statements and Declarations 照抄。

## 二、这本期刊的特别要求（已按要求做了）

- 正文是压缩版（比 JMIR 那份短约 600 词）：删的是重复的话和次要细节，没有删任何预先登记的结论；被删的细节都在 Online Resource 1 或 JMIR 版里。
- 报告规范：期刊要求上传对应的清单，临床预测模型用 TRIPOD+AI。已填好，作为 Online Resource 2（ESM_2.pdf）。
- AI 使用：期刊要求在 Methods 写清工具、版本、日期、使用方式、提示词（或代表性提示词）、设置和人工核查。Methods 的 "Use of generative AI" 写了工具、模型版本（Claude Fable 5.1/5.2、Claude Opus 5.5，取自提交记录署名）、日期、使用方式（Claude Code 命令行、默认设置）和人工核查；三条代表性指令（中文原话的英译转述）在 Online Resource 3。
- 补充材料用 PDF，文件名 ESM_1/2/3，每个文件开头有文章标题、期刊名、作者和通讯作者信息（期刊要求）。
- 图：正文里嵌入了图；单独上传时**每张图只传 EPS**（矢量），600 dpi TIFF 是备用。图注以粗体 "Fig. 1" 开头、末尾不加句号。
- 图 3、图 4 原宽约 184、195 毫米，比 Springer 双栏最大宽度 174 毫米宽，排版时会缩小，图里 7 磅的字会变成约 6.3 磅；如果编辑部要求，我再按 174 毫米重画。
- 参考文献：Springer 格式（方括号编号，作者最多列 6 位，DOI 写成链接）。

## 三、已知风险（要心里有数）

- 期刊列的"直接退稿原因"里有一条 **"poor English or AI-generated text"**。我们的稿子大部分由 AI 起草，并如实声明了。编辑可能因此退稿；如果你想降低这个风险，可以请人通读改写一遍语言。
- 另一条是"只比较算法 X 和 Y、不讲实际部署"的论文。我们讲了成本（每例约 1 美分）和泄漏、外部测试，但没有临床部署。
"""
    return f"""# 投稿前要做的事 — {fmt["name"]}

出版社：BMJ；投稿系统：ScholarOne（期刊主页 {fmt["site"]} 的 Submit manuscript）。
影响因子：{fmt["impact"]}。
文章类型：Original research（正文 ≤ 3,000 词、结构化摘要 ≤ 250 词、参考文献 ≤ 30 条、正文图表合计 ≤ 5 个）。现在正文 {facts["main_words"]} 词、摘要 {facts["abstract_words"]} 词、参考文献 {facts["n_refs"]} 条、正文图表 5 个。
费用：开放获取期刊，录用后付文章处理费 2,460 英镑（不含增值税）；可以在投稿时申请减免（BMJ 对低收入国家作者全免，其他情况可申请部分减免）。

## 一、要你确认的

{common}
9. **Guarantor（对全文负责的作者）**：BMJ 要求写一位，现在写的是 Peng Chen。不对就告诉我。
10. **投稿人必须有 ORCID**（BMJ 强制）：叶和陈鹏都有，用其中一人的账号投。
11. **被拒后是否同意转投 BMJ 其他期刊**（如 BMJ Open）：投稿信里写的是"同意"。

## 二、这本期刊的特别要求（已按要求做了）

- 正文是大幅压缩版（{facts["main_words"]} 词，JMIR 版约 4,550 词）：删的是重复的话、次要分析和部分细节，**没有删任何预先登记的结论**（12 条主要结论 9 条成立、3 条不成立，全部还在）；删掉的次要结果都在补充材料或 JMIR 版里。
- 正文只放 5 个图表：表 1（数据集）、图 1（方法示意）、图 2（遮蔽的影响）、图 3（agent 对比自己的模型）、表 2（三项预先登记测试）。其余 3 图 3 表移到补充材料 1 的 S14，正文里称为 online supplemental figure/table A–C。
- 摘要后加了 BMJ 要求的 "Key messages" 三问。
- Methods 里加了 BMJ 要求的 "Patient and public involvement"。
- AI 使用：按 BMJ 政策，在 Contributors 里致谢、在 Methods 里说明，详细的是补充材料 3。
- 图单独上传：**每张图只传一份，用 PDF（矢量）**；1200 dpi TIFF 是备用（BMJ 对线条图要求 1200 dpi）。图注放在稿子末尾，图注里没有提颜色（BMJ 要求）。
- 关键词用的是 MeSH 词。
- 参考文献：BMJ 的 Vancouver 格式（前三位作者 + et al，带 DOI）。
"""


def write_other(fmt: dict[str, Any]) -> dict[str, Any]:
    d = OUT / fmt["folder"]
    if d.exists():
        shutil.rmtree(d)
    supp_dir = "04_online_resources" if fmt["key"] == "joms" else "04_supplementary"
    for sub in ("01_manuscript", "02_cover_letter", "03_figures", supp_dir):
        (d / sub).mkdir(parents=True)
    text, supp, facts = manuscript_other(fmt)
    # figures beside the sources so pandoc can embed them
    for sub in ("01_manuscript", supp_dir):
        (d / sub / "figures").mkdir()
        for f in FIGURES:
            shutil.copy(FIG_PLAIN / f"{f}.png", d / sub / "figures" / f"{f}.png")
    ms = d / "01_manuscript" / "manuscript.md"
    ms.write_text(size_columns(text))
    pandoc(ms, d / "01_manuscript" / "manuscript.docx", d / "01_manuscript")
    ms.rename(d / "01_manuscript" / "manuscript_source.md")
    shutil.rmtree(d / "01_manuscript" / "figures")
    figs = figure_files(fmt, facts["labels"], d / "03_figures")
    # supplementary files, as PDF
    s = [fmt["supp"].format(n=k) for k in (1, 2, 3)]
    s = [x[0].upper() + x[1:] for x in s]
    names = (
        ["ESM_1.pdf", "ESM_2.pdf", "ESM_3.pdf"]
        if fmt["key"] == "joms"
        else [
            "Supplementary_file_1.pdf",
            "Supplementary_file_2_TRIPOD-AI.pdf",
            "Supplementary_file_3_AI_use.pdf",
        ]
    )
    tripod = (SRC / "tripod_ai_checklist.md").read_text()
    tripod = tripod.replace("{S}", s[0]).replace("{DECL}", fmt["decl"])
    tripod = f'---\ntitle: "{s[1]}. TRIPOD+AI checklist"\n---\n\n' + header_block(fmt) + tripod
    ai = (SRC / "ai_use_appendix.md").read_text()
    ai = re.sub(r'title: ".*?"', f'title: "{s[2]}. Use of generative AI in this work"', ai, count=1)
    head_end = ai.index("---", 3) + 3
    ai = ai[:head_end] + "\n\n" + header_block(fmt) + ai[head_end:].lstrip("\n")
    ai = ai.replace("Multimedia Appendix 1", s[0])
    for name, md in zip(names, (supp, tripod, ai), strict=True):
        md_to_pdf(size_columns(md), d / supp_dir / name, d / supp_dir)
    shutil.rmtree(d / supp_dir / "figures")
    (d / "_sources").mkdir()
    for name, md in zip(names, (supp, tripod, ai), strict=True):
        (d / "_sources" / name.replace(".pdf", ".md")).write_text(md)
    cl = d / "02_cover_letter" / "cover_letter.md"
    cl.write_text(cover_letter_other(fmt, facts))
    pandoc(cl, cl.with_suffix(".docx"), PAPER)
    (d / "README.md").write_text(readme_other(fmt, facts, figs))
    (d / "BEFORE_SUBMISSION.md").write_text(checklist_other(fmt, facts))
    lines = [
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(d)}"
        for p in sorted(q for q in d.rglob("*") if q.is_file() and q.name != "CHECKSUMS.sha256")
    ]
    (d / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n")
    facts["text"], facts["supp"], facts["cover"] = text, supp, cl.read_text()
    return facts


def run_checks(fmt: dict[str, Any], facts: dict[str, Any]) -> list[str]:
    name = fmt["key"]
    problems = []
    if facts["main_words"] > fmt["word_limit"]:
        problems.append(f"{name}: main text {facts['main_words']} words > {fmt['word_limit']}")
    if facts["abstract_words"] > fmt["abstract_limit"]:
        problems.append(
            f"{name}: abstract {facts['abstract_words']} words > {fmt['abstract_limit']}"
        )
    if name == "bmj" and facts["n_refs"] > 30:
        problems.append(f"bmj: {facts['n_refs']} references > 30")
    allowed = {
        str(fmt["word_limit"]),
        f"{fmt['word_limit']:,}",
        str(facts["main_words"]),
        str(facts["abstract_words"]),
    }
    allowed |= {"1", "2", "3", "12", "9", "2026", "2025", "2024"}
    problems += check_numbers(
        f"{name} body", facts["raw"], {"5.1", "5.2", "5.5"}
    )  # model versions in the AI paragraph
    problems += check_numbers(f"{name} abstract", facts["abstract"])
    if name == "bmj":
        problems += check_numbers("bmj key messages", (SRC / "bmj_key_messages.md").read_text())
    cover_main = facts["cover"].split("Yours sincerely")[0]
    problems += check_numbers(f"{name} cover letter", cover_main, allowed)
    problems += check_p(f"{name} manuscript", facts["text"])
    problems += check_p(f"{name} supplement", facts["supp"])
    leftover = re.findall(r"\[\[[^\]]+\]\]|\{S\}|\{DECL\}", facts["text"] + facts["supp"])
    if leftover:
        problems.append(f"{name}: unreplaced placeholders {set(leftover)}")
    cited = {n for m in CITE.finditer(facts["text"] + facts["supp"]) for n in _expand(m.group(1))}
    if cited != set(range(1, facts["n_refs"] + 1)):
        problems.append(
            f"{name}: citations {sorted(cited)} do not match {facts['n_refs']} references"
        )
    return problems


def main() -> None:
    OUT.mkdir(exist_ok=True)
    shutil.copy(SRC / "JOURNAL_CHOICE.md", OUT / "JOURNAL_CHOICE.md")
    for j in JOURNALS:
        write(j)
        print("wrote", OUT / j["folder"])
    if UNPAIRED:
        print("P values converted from their printed value (no paired count nearby):")
        for u in sorted(set(UNPAIRED)):
            print("  ", u)
    problems: list[str] = []
    make_plain_figures()
    for f in FIGURES:  # the figures' own p values, read back from the PDFs
        txt = subprocess.run(
            ["pdftotext", "-layout", str(FIG_PLAIN / f"{f}.pdf"), "-"],
            capture_output=True,
            text=True,
        ).stdout
        problems += check_figure_p(f, txt)
    for fmt in OTHER:
        facts = write_other(fmt)
        print(
            "wrote",
            OUT / fmt["folder"],
            f"(main text {facts['main_words']} words, abstract {facts['abstract_words']}, {facts['n_refs']} references)",
        )
        problems += run_checks(fmt, facts)
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  ", p)
        raise SystemExit(1)
    print("checks passed: numbers from the sources, p values, word limits, citations, placeholders")


if __name__ == "__main__":
    main()

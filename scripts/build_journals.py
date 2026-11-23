# ruff: noqa: E501  (long strings: addresses, cover-letter and checklist text)
"""Build the submission folders for the three JMIR Publications journals from docs/paper.

    uv run python scripts/build_journals.py

Reads docs/paper/{manuscript,supplementary,references}.md and docs/paper/journal_sources/,
and writes docs/paper/journals/<NN_Journal>/ (not tracked by git): the manuscript in JMIR
format (title page, structured abstract, unnumbered IMRD sections, figures and tables inline,
P values in JMIR style recomputed from the paired counts, AMA references), Multimedia
Appendices, the cover letter, figure files, a pre-submission checklist and checksums.

Content is never edited here beyond format: every number comes from manuscript.md, and every
P value attached to a paired count is recomputed from that count.
"""

import hashlib
import re
import shutil
import subprocess
from math import comb
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "paper"
SRC = PAPER / "journal_sources"
OUT = PAPER / "journals"

AUTHORS: list[dict[str, Any]] = [
    {
        "name": "Shaopei Ye",
        "aff": [1],
        "email": "shaopeiye55@gmail.com",
        "orcid": "0009-0006-3598-0469",
    },
    {"name": "Lan Wang", "aff": [2], "email": None, "orcid": None},
    {
        "name": "Peng Chen",
        "aff": [3],
        "email": "cpeng960@gmail.com",
        "orcid": "0009-0001-1105-6638",
    },
]
AFFILIATIONS = {
    1: "Universitat de Barcelona, Barcelona, Spain",
    2: "Department of Otorhinolaryngology Head and Neck Surgery, Chengdu Fifth People's Hospital, Chengdu, Sichuan, China",
    3: "Department of Otorhinolaryngology, The Second People's Hospital of Meishan, No. 288 Dongpo Avenue South Section 4, Dongpo District, Meishan 620020, Sichuan Province, China",
}
CORRESPONDING = 0  # index into AUTHORS

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
        "tier": "冲一冲：分最高（8.2），选择性也最高；被拒时可同意转给 JMIR AI 或 JMIR Medical Informatics 继续审（JMIR 的转投机制）",
    },
    {
        "folder": "02_JMIR_AI",
        "name": "JMIR AI",
        "short": "JMIR AI",
        "impact": "6.1 (2025 JIF, Journal Citation Reports 2026; Q1)",
        "apf": "US $1985",
        "site": "https://ai.jmir.org",
        "why": (
            "JMIR AI focuses on the development and rigorous evaluation of artificial intelligence in health. Our "
            "manuscript evaluates a language-model agent with the controls that such evaluations often lack — masking "
            "of each test case's source, prespecified plans and tests outside the development data — and we have "
            "completed the reporting checklist the journal recommends (Multimedia Appendix 2)."
        ),
        "tier": "最对口：专门发 AI 用于医疗的研究，6.1 分、Q1，文章处理费最低",
    },
    {
        "folder": "03_JMIR_Medical_Informatics",
        "name": "JMIR Medical Informatics",
        "short": "JMIR Med Inform",
        "impact": "5.0 (2025 JIF, Journal Citation Reports 2026)",
        "apf": "US $2750",
        "site": "https://medinform.jmir.org",
        "why": (
            "JMIR Medical Informatics publishes evaluations of clinical decision support and of language models in "
            "clinical informatics. Our manuscript reports such an evaluation for rare disease diagnosis, with the "
            "benchmark-leakage and external-testing issues that matter for any phenotype-based decision support tool."
        ),
        "tier": "最稳：大模型评测类文章发得多，5.0 分",
    },
]

TITLE = (
    "Source-Paper Masking and Prespecified External Tests of a Low-Cost Tool-Using Agent for "
    "Rare Disease Diagnosis: Evaluation Study"
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
    "3.2": "The First Version on Masked Held-Out Cases",
    "3.3": "A Failure That Only External Patients Exposed",
    "3.4": "Prespecified Tests of the Revised Agent",
    "3.5": "What the Lead Is Made Of",
    "3.6": "Comparison With a Frontier Model, and Cost",
}
CROSS_REFS = {
    "Section 2.4": "the Agent section",
    "Section 2.5": "the Comparators section",
    "Section 2.6": "the Plans and Records section",
    "Section 3.4": "the Prespecified Tests of the Revised Agent section",
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
    "Acknowledgements": "Acknowledgments",
}
ABBREVIATIONS = [
    ("CI", "confidence interval"),
    ("HPO", "Human Phenotype Ontology"),
    ("LIRICAL", "Likelihood Ratio Interpretation of Clinical Abnormalities"),
    ("LLM", "large language model"),
    ("OMIM", "Online Mendelian Inheritance in Man"),
    ("PEDIA", "Prioritization of Exome Data by Image Analysis"),
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
        full[rest[:50]] = authors
    out = []
    for num, entry in items:
        authors, _, rest = entry.partition(". ")
        older = full.get(rest[:50])
        if older and "et al" not in older and _named(older) > _named(authors):
            authors = older
        out.append(f"{num}. {authors}. {rest}")
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
        "collected from humans; ethics review was therefore not sought.\n\n"
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
        "case's source was masked. One recent study removed the leakage pathway before its evaluation [13]; our "
        "results suggest that, where it is not removed, it favors tools that read the annotations."
    )
    new = (
        "## Discussion\n\n### Principal Results\n\n"
        + opening
        + "\n\n"
        + pick("Tools and model")
        + "\n\n"
        + pick("Retrieving the right entry")
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
        sup = ",".join(str(x) for x in a["aff"]) + ("\\*" if k == CORRESPONDING else "")
        names.append(f"{a['name']}^{sup}^")
    lines = [", ".join(names), ""]
    lines += [f"^{k}^ {v}" for k, v in AFFILIATIONS.items()] + [""]
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

The code, the frozen case lists, the evaluation plans with their commit history, and per-case outcomes of most reported runs are available in the project repository [https://github.com/pipi0616/rare-disease-agent]. Every dataset used is public and pinned by version and checksum in the repository. The texts of the post-cutoff case reports are not redistributed, because some licenses are noncommercial; the repository lists each paper, the sentences kept and a checksum of the kept text, from which the set can be rebuilt.

## Authors' Contributions

Conceptualization: SY, PC. Methodology: SY. Software: SY. Formal analysis: SY. Data curation: SY. Visualization: SY. Investigation (clinical interpretation): PC, LW. Supervision: LW, PC. Writing – original draft: SY. Writing – review & editing: SY, LW, PC.

## Abbreviations

{chr(10).join(f"{a}: {b}" for a, b in ABBREVIATIONS)}

## Multimedia Appendix 1

Supplementary methods and results (sections S1–S13).

## Multimedia Appendix 2

Completed reporting checklist (Luo et al, 2016).

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
    text = text.replace("p-values", "P values").replace("p-value", "P value")
    text = convert_p(text)
    return american(text)


def supplement() -> str:
    t = (PAPER / "supplementary.md").read_text()
    t = re.sub(
        r'title: ".*?"',
        'title: "Multimedia Appendix 1. Supplementary methods and results"',
        t,
        count=1,
    )
    t = re.sub(r'subtitle: ".*?"', f'subtitle: "{TITLE}"', t, count=1)
    t = t.replace("Sections 3.4–3.5", "the sections on the prespecified tests")
    t = t.replace("Section 2.4", "the Agent section").replace("Section 3.3", "the held-out results")
    t = t.replace("(p from 0.23 to 0.89)", "(*P* from .23 to .89)")
    t = convert_p(t)
    return american(t)


def cover_letter(journal: dict[str, str]) -> str:
    c = AUTHORS[CORRESPONDING]
    return f"""[Date]

To the Editor, {journal["name"]}

Dear Editor,

We submit for your consideration the Original Paper **"{TITLE}"**.

Language-model agents are now reported to name a rare disease from a patient's phenotype with striking accuracy. Three things make such reports hard to read: the public test cases are case reports that phenotype knowledge bases were curated from; a model may have memorized a public benchmark; and published cases are not patients as a clinic or a laboratory records them. Our manuscript measures one such agent with these 3 problems in view, and reports what the measurement shows, with analyses that locate where the agent's lead comes from.

{journal["why"]}

What we believe is useful to your readers:

1. **The size of the leak.** Hiding each test case's own source paper from the knowledge base halves the first-place accuracy of LIRICAL, a published and maintained tool, on 840 held-out published cases (63.2% to 30.1%).
2. **External tests catch what held-out tests miss.** The agent's first version passed its held-out test and then lost to its own model on a clinic's and a registry's patients; its traces showed a ranking blind to prevalence. Of 12 prespecified primary claims, 9 held and 3 failed, and all are reported.
3. **Three prespecified tests on cases never used in development.** Scored by identifier, the agent ranked the confirmed disease first more often than its own model asked directly on 146 MyGene2 patients (52.1% vs 7.5%), 577 CADA cases (23.6% vs 14.7%) and 240 case reports published after the model's training cutoff (19.6% vs 8.8%). We report where the lead is not established: on the case reports when judged by disease name, for the 205 patients of CADA's collaborators' cohorts, and against GPT-6.1 asked directly on MyGene2.

The manuscript is original, has not been published, and is not under consideration elsewhere; it has not been posted as a preprint. It does not overlap with other published or submitted work by the authors. All authors have approved the manuscript and meet the criteria for authorship. Only public, deidentified data were used, and no ethics review was required.

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
- Built by `scripts/build_journals.py` from `docs/paper/` (commit recorded in git); do not edit the .docx by hand — change the sources and rebuild.

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

1. **作者顺序和通讯作者**：现在是 Shaopei Ye、Lan Wang、Peng Chen，通讯作者 Shaopei Ye。上一篇 HEARS-LM 的通讯作者是王兰，这篇要不要改，你定。
2. **单位**：叶：Universitat de Barcelona；王兰：成都市第五人民医院耳鼻咽喉头颈外科；陈鹏：眉山市第二人民医院耳鼻喉科（都照上一篇写的）。
3. **王兰的 ORCID**：JMIR 要求所有作者在录用时都有 ORCID。王兰还没有，要她在 orcid.org 免费注册一个。
4. **作者贡献（CRediT）**：稿子里是参照上一篇写的初稿，请三位确认。
5. **基金**：写的是"没有专门资助"。有的话告诉我。
6. **利益冲突**：写的是"无"。
7. **伦理**：写的是"只用公开、去标识的数据，没有申请伦理审查"。如果两家医院的作者单位要求出具豁免说明，告诉我。
8. **投稿信里的两句声明**："没有发过预印本""和作者已发表或在投的其他论文没有重叠"（HEARS-LM 是另一个题目）。不对就告诉我。

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
- 正文约 4,400 词；JMIR 原创论文没有查到硬性字数上限。
"""


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


if __name__ == "__main__":
    main()

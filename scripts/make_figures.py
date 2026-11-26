# ruff: noqa: E501  (figure labels are long strings)
"""The paper's figures, drawn from the per-case outcome tables committed in docs/.

    uv run python scripts/make_figures.py            # every figure whose data exists
    uv run python scripts/make_figures.py fig3 fig5  # some of them

Each figure is written to docs/paper/figures/ as PNG (300 dpi) and PDF, with p values in
JMIR style (P<.001, P=.07). FIG_P_STYLE=plain writes them as the manuscript's text does
(p < 0.001, p = 0.065), and FIG_OUT=<dir> writes elsewhere; build_journals.py uses both for
the Springer and BMJ packages. Nothing is typed
in by hand that a table holds: rates and their 95% Wilson intervals are computed here
from the same hits tables the text quotes. The few numbers that exist only as recorded
runs' summaries (the unmasked development run) are named where they are used.

One colour per kind of system, the same in every figure: the agent, a model asked
directly, a tool that calls no model; anything else is grey. Values are written beside
the marks, so no reading depends on colour.
"""

import csv
import json
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = Path(os.environ["FIG_OUT"]) if os.environ.get("FIG_OUT") else DOCS / "paper" / "figures"
P_STYLE = os.environ.get("FIG_P_STYLE", "jmir")

AGENT, MODEL, TOOL, OTHER = "#2a78d6", "#eb6834", "#1baf7a", "#4a4a48"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
KIND = {"agent": AGENT, "model": MODEL, "tool": TOOL, "other": OTHER}
KIND_NAME = {
    "agent": "agent (model with tools)",
    "model": "model asked directly",
    "tool": "tool, no model",
    "other": "other system",
}

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8,
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.6,
        "axes.labelcolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "pdf.fonttype": 42,
        "mathtext.fontset": "custom",
        "mathtext.it": "Helvetica:italic",
        "mathtext.rm": "Helvetica",
    }
)


def wilson(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def hits_table(name: str) -> list[dict[str, str]]:
    with (DOCS / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def count(rows: list[dict[str, str]], system: str, k: int = 1) -> tuple[int, int]:
    return sum(r[f"{system}@{k}"] == "1" for r in rows), len(rows)


def save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{suffix}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / name}.png and .pdf")


def interval_rows(
    ax: plt.Axes,
    rows: list[tuple[str, int, int, str]],
    *,
    xmax: float = 100,
    title: str | None = None,
    xlabel: str = "confirmed disease ranked first (%)",
) -> None:
    """One row per system: its rate as a dot, its 95% interval as a line, the value
    written at the line's end. rows: (label, hits, n, kind), drawn top to bottom."""
    for i, (_, hits, n, kind) in enumerate(rows):
        y = len(rows) - 1 - i
        rate = 100 * hits / n
        low, high = (100 * v for v in wilson(hits, n))
        ax.plot([low, high], [y, y], color=KIND[kind], lw=2, solid_capstyle="round", zorder=2)
        ax.plot(
            [rate],
            [y],
            "o",
            ms=6.5,
            color=KIND[kind],
            mec=SURFACE,
            mew=1.4,
            zorder=3,
            clip_on=False,
        )
        ax.text(
            high + xmax * 0.015, y, f"{rate:.1f}", va="center", ha="left", color=INK, fontsize=8
        )
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)])
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(0, xmax)
    ax.xaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel)
    if title:
        ax.set_title(title, loc="left", fontsize=8.5, color=INK, pad=6)


def kind_legend(ax_or_fig: plt.Axes | plt.Figure, kinds: list[str], **where: object) -> None:
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            ms=6,
            color=KIND[k],
            lw=2,
            mec=SURFACE,
            mew=1.2,
            label=KIND_NAME[k],
        )
        for k in kinds
    ]
    ax_or_fig.legend(handles=handles, frameon=False, fontsize=7.5, handlelength=1.6, **where)  # type: ignore[arg-type]


# ── figure 1: how a case is asked, and what is hidden while it is ────────────


def fig1() -> None:
    fig, ax = plt.subplots(figsize=(7.1, 3.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    ax.axis("off")
    soft = "#f6f5f2"

    def box(
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        edge: str = INK2,
        face: str = SURFACE,
        weight: str = "normal",
        style: object = "solid",
    ) -> None:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0,rounding_size=1.0",
                lw=0.9,
                ec=edge,
                fc=face,
                linestyle=style,
            )
        )
        ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            fontsize=7,
            color=INK,
            fontweight=weight,
            linespacing=1.3,
        )

    def arrow(x1: float, y1: float, x2: float, y2: float, style: str = "-|>") -> None:
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle=style,
                mutation_scale=7,
                lw=0.9,
                color=INK2,
                shrinkA=0,
                shrinkB=0,
            )
        )

    # the flow, left to right
    box(2, 34, 18, 12, "Patient's findings\nas HPO terms\n(or a note, read\ninto terms first)")
    box(26, 41.5, 23, 6.5, "1  The model answers\nfrom its own knowledge", edge=MODEL)
    box(26, 32, 23, 6.5, "2  Tools rank every disease\nand check the leaders", edge=TOOL)
    box(
        54,
        33,
        25,
        14,
        "3  The agent weighs both\nlists: each candidate with\nevidence and prevalence;\nup to eight model calls,\ntools on demand",
        edge=AGENT,
        weight="bold",
    )
    box(84, 35, 14, 10, "Up to ten\ndiseases, each\nwith an identifier\nand a reason")
    arrow(20.4, 42, 25.6, 44.5)
    arrow(20.4, 38, 25.6, 35.5)
    arrow(49.4, 44.5, 53.6, 42)
    arrow(49.4, 35.5, 53.6, 38)
    arrow(79.4, 40, 83.6, 40)

    # what the tools are, and what they read
    box(
        26,
        17.5,
        72,
        8.5,
        "rank_diseases   ·   check_match   ·   lookup_disease\nfind_disease   ·   find_similar_patients   ·   search_disease_texts",
        edge=TOOL,
    )
    box(
        26,
        4,
        72,
        8.5,
        "Pinned knowledge: HPO disease annotations (OMIM; Orphanet's merged in for v2),\nOrphanet prevalence classes, 6,014 published patients,\ndisease descriptions (Orphanet, MedlinePlus Genetics)",
        edge=GRID,
        face=soft,
    )
    arrow(37.5, 31.6, 37.5, 26.4)
    arrow(66.5, 32.6, 66.5, 26.4, style="<|-|>")
    arrow(62, 17.1, 62, 12.9)

    # the mask
    box(
        2,
        4,
        18,
        22,
        "While a case is\nasked, its known\nsource paper is\nmasked from all that\nthe tools read.\nAfterwards, every\ntool output is\naudited for it.",
        edge=INK,
        face=soft,
        style=(0, (3, 2)),
    )
    arrow(20.4, 8.2, 25.6, 8.2)
    save(fig, "fig1_design")


# ── figure 2: what the mask removes ──────────────────────────────────────────


def fig2() -> None:
    rows840 = hits_table("comparison_hits.tsv")
    pairs = [
        # (label, masked (hits, n), unmasked (hits, n))
        (
            "LIRICAL\nfirst place, 840 held-out cases",
            count(rows840, "lirical"),
            count(rows840, "lirical (unmasked)"),
        ),
        (
            "Rank, then check\nfirst place, 840 held-out cases",
            count(rows840, "rank-then-check"),
            count(rows840, "rank-then-check (unmasked)"),
        ),
        (
            "Phenotype similarity\nfirst place, 840 held-out cases",
            count(rows840, "phenotype-rank"),
            count(rows840, "phenotype-rank (unmasked)"),
        ),
        (
            "Phenotype similarity\ntop ten, 840 held-out cases",
            count(rows840, "phenotype-rank", 10),
            count(rows840, "phenotype-rank (unmasked)", 10),
        ),
    ]
    fig, ax = plt.subplots(figsize=(4.6, 2.5))
    for i, (_, masked, unmasked) in enumerate(pairs):
        y = len(pairs) - 1 - i
        a, b = 100 * masked[0] / masked[1], 100 * unmasked[0] / unmasked[1]
        ax.plot([a, b], [y, y], color=GRID, lw=2, zorder=1, solid_capstyle="round")
        ax.plot([b], [y], "o", ms=6.5, mfc=SURFACE, mec=TOOL, mew=1.6, zorder=3)
        ax.plot([a], [y], "o", ms=6.5, color=TOOL, mec=SURFACE, mew=1.4, zorder=3)
        ax.text(a - 2.2, y, f"{a:.1f}", ha="right", va="center", color=INK)
        ax.text(b + 2.2, y, f"{b:.1f}", ha="left", va="center", color=INK)
    ax.set_yticks(range(len(pairs)))
    ax.set_yticklabels([p[0] for p in reversed(pairs)], linespacing=1.15)
    ax.set_ylim(-0.6, len(pairs) - 0.4)
    ax.set_xlim(0, 100)
    ax.xaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("cases with the confirmed disease found (%)")
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            ms=6,
            color=TOOL,
            lw=0,
            mec=SURFACE,
            mew=1.2,
            label="the case's own paper masked",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            ms=6,
            mfc=SURFACE,
            mec=TOOL,
            mew=1.5,
            lw=0,
            label="unmasked (own paper left in)",
        ),
    ]
    ax.legend(
        handles=handles,
        frameon=False,
        fontsize=7.5,
        loc="lower center",
        bbox_to_anchor=(0.42, 1.0),
        ncol=2,
        columnspacing=1.4,
        handletextpad=0.3,
    )
    save(fig, "fig2_leakage")


# ── figure 3: the held-out cases ─────────────────────────────────────────────


def fig3() -> None:
    all840 = hits_table("comparison_hits.tsv")
    part200 = hits_table("comparison_llm_hits.tsv")
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.1, 2.9), gridspec_kw={"wspace": 0.95})
    interval_rows(
        left,
        [
            ("Agent (v1.0)", *count(all840, "agent"), "agent"),
            ("Fixed pipeline", *count(all840, "fixed-pipeline"), "other"),
            ("Rank, then check", *count(all840, "rank-then-check"), "tool"),
            ("LIRICAL", *count(all840, "lirical"), "tool"),
            ("Phenotype similarity", *count(all840, "phenotype-rank"), "tool"),
            ("Same model, asked directly", *count(all840, "llm-direct"), "model"),
        ],
        xmax=60,
        title="a   840 held-out cases, one per paper",
    )
    interval_rows(
        right,
        [
            ("Agent (v1.0)", *count(part200, "agent"), "agent"),
            ("GPT-6.1, asked directly", *count(part200, "gpt"), "model"),
            ("LIRICAL", *count(part200, "lirical"), "tool"),
            ("Gemini 4, asked directly", *count(part200, "gemini"), "model"),
            ("Claude Sonnet 5.5, asked directly", *count(part200, "claude"), "model"),
            ("Same model, asked directly", *count(part200, "llm-direct"), "model"),
            ("DeepRare, same model (unmasked)", *count(part200, "deeprare"), "other"),
        ],
        xmax=60,
        title="b   a fixed random 200 of them",
    )
    kind_legend(
        fig,
        ["agent", "model", "tool", "other"],
        loc="lower center",
        ncol=4,
        bbox_to_anchor=(0.5, -0.13),
        columnspacing=1.6,
    )
    save(fig, "fig3_heldout")


# ── figure 4: the agent against its own model, on every test ─────────────────


def paired_rows(
    ax: plt.Axes,
    rows: list[tuple[str, tuple[int, int], tuple[int, int], str]],
    xmax: float,
    by_name: list[tuple[float, float]] | None = None,
) -> None:
    """One row per test: the agent's rate and the model's, each with its interval; the
    paired result written at the right. rows: (label, agent, model, note). by_name: the two
    rates judged by disease name, drawn as open circles without intervals."""
    for i, (_, agent, model, note) in enumerate(rows):
        y = len(rows) - 1 - i
        if by_name is not None:
            for rate, color, dy in ((by_name[i][0], AGENT, 0.16), (by_name[i][1], MODEL, -0.16)):
                ax.plot(
                    [rate],
                    [y + dy],
                    "o",
                    ms=6,
                    mfc=SURFACE,
                    mec=color,
                    mew=1.4,
                    zorder=4,
                    clip_on=False,
                )
        for (hits, n), color, dy in ((agent, AGENT, 0.16), (model, MODEL, -0.16)):
            rate = 100 * hits / n
            low, high = (100 * v for v in wilson(hits, n))
            ax.plot(
                [low, high], [y + dy, y + dy], color=color, lw=2, solid_capstyle="round", zorder=2
            )
            ax.plot(
                [rate],
                [y + dy],
                "o",
                ms=6,
                color=color,
                mec=SURFACE,
                mew=1.3,
                zorder=3,
                clip_on=False,
            )
        ax.text(
            xmax * 1.02, y, note, va="center", ha="left", color=INK, fontsize=7.5, linespacing=1.2
        )
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], linespacing=1.15)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(0, xmax)
    ax.xaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def sign_test(wins: int, losses: int) -> float:
    from math import comb

    n = wins + losses
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(wins, losses) + 1)) / 2**n)


def pair_note(rows: list[dict[str, str]], agent: str, model: str) -> str:
    won = sum(r[f"{agent}@1"] == "1" and r[f"{model}@1"] != "1" for r in rows)
    lost = sum(r[f"{model}@1"] == "1" and r[f"{agent}@1"] != "1" for r in rows)
    p = sign_test(won, lost)
    return f"{won} : {lost}\n" + p_text(p)


def p_text(p: float) -> str:
    """JMIR style: P<.001; three decimals below .01; otherwise two decimals; P>.99.
    Plain style, as the manuscript's text: p < 0.001; three decimals below 0.1; else two."""
    if P_STYLE == "plain":
        if p < 0.001:
            return "p < 0.001"
        return f"p = {p:.{3 if p < 0.1 else 2}f}"
    if p < 0.001:
        value = "<.001"
    elif float(f"{p:.3f}") < 0.01:
        value = "=" + f"{p:.3f}"[1:]
    elif float(f"{p:.2f}") >= 1:
        value = ">.99"
    else:
        value = "=" + f"{p:.2f}"[1:]
    return r"$\it{P}$" + value


def fig4() -> None:
    temporal = hits_table("temporal_hits.tsv")
    hms = hits_table("rarebench_hms_hits.tsv")
    ramedis = hits_table("rarebench_ramedis_hits.tsv")
    mme = hits_table("rarebench_mme_hits.tsv")
    held = hits_table("comparison_hits.tsv")

    def row(
        label: str, rows: list[dict[str, str]], agent: str
    ) -> tuple[str, tuple[int, int], tuple[int, int], str]:
        return (
            label,
            count(rows, agent),
            count(rows, "llm-direct"),
            pair_note(rows, agent, "llm-direct"),
        )

    first = [
        row("Held-out published cases\n(n = 840)", held, "agent"),
        row("Temporal: published after\nthe model's cutoff (n = 47)", temporal, "agent"),
        row("HMS, a clinic's patients\n(n = 88)", hms, "agent"),
        row("RAMEDIS, a metabolic\nregistry (n = 624)", ramedis, "agent"),
    ]
    second = [
        row("Published after the model's\ncutoff (n = 47)", temporal, "hypothesis-agent"),
        row("MME, published cases\n(n = 40)", mme, "hypothesis-agent"),
    ]
    new = []
    by_name: list[tuple[float, float]] = []
    for label, name, agent in (
        (
            "MyGene2, patients shared by\nfamilies and clinicians (n = {n})",
            "exam_mygene2_hits.tsv",
            "agent-v1.1",
        ),
        (
            "CADA test, laboratories'\nand clinics' cases (n = {n})",
            "exam_cada-test_hits.tsv",
            "agent-v1.1",
        ),
        (
            "Case reports after the cutoff,\ncut before the diagnosis (n = {n})",
            "exam_casereports-exam_hits.tsv",
            "agent-v2",
        ),
    ):
        if (DOCS / name).exists():
            rows = hits_table(name)
            lenient = DOCS / name.replace("exam_", "exam_lenient_", 1).replace("_hits.tsv", ".json")
            judged = json.loads(lenient.read_text())
            a_hits = sum(r.get(agent) == 1 for r in judged)
            m_hits = sum(r.get("llm-direct") == 1 for r in judged)
            won = sum(r.get(agent) == 1 and r.get("llm-direct") != 1 for r in judged)
            lost = sum(r.get("llm-direct") == 1 and r.get(agent) != 1 for r in judged)
            by_name.append((100 * a_hits / len(judged), 100 * m_hits / len(judged)))
            lab, a, m, note = row(label.format(n=len(rows)), rows, agent)
            note = (
                note.replace("\n", ", ")
                + f"\nby name {won} : {lost}, "
                + p_text(sign_test(won, lost))
            )
            new.append((lab, a, m, note))
    del second  # v1.1a, run without a prespecified comparison: Supplementary Table S11
    groups = [("a   v1.0, prespecified tests", first)]
    if new:
        groups.append(
            ("b   Revised agent, prespecified tests: v1.1 (patients), v2 (case reports)", new)
        )
    heights = [len(g[1]) for g in groups]
    fig, axes = plt.subplots(
        len(groups),
        1,
        figsize=(6.0, 0.5 * sum(heights) + 0.62 * len(groups) + 0.3),
        gridspec_kw={"height_ratios": heights, "hspace": 0.62},
    )
    for k, (ax, (title, rows)) in enumerate(zip(list(axes), groups, strict=True)):
        paired_rows(ax, rows, xmax=80, by_name=by_name if k == 1 else None)
        ax.set_title(title, loc="left", fontsize=8.5, color=INK, pad=5)
        ax.text(
            80 * 1.02,
            len(rows) - 0.42,
            "agent : model, cases\nonly one gets right",
            fontsize=7.5,
            color=INK2,
            va="bottom",
            ha="left",
            linespacing=1.15,
        )
    list(axes)[-1].set_xlabel("confirmed disease ranked first (%), with 95% interval")
    handles = [
        Line2D([0], [0], marker="o", ms=6, color=AGENT, lw=2, mec=SURFACE, mew=1.2, label="agent"),
        Line2D(
            [0],
            [0],
            marker="o",
            ms=6,
            color=MODEL,
            lw=2,
            mec=SURFACE,
            mew=1.2,
            label="the same model asked directly",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            ms=6,
            color=INK2,
            lw=0,
            mfc=SURFACE,
            mec=INK2,
            mew=1.4,
            label="open: judged by disease name (b)",
        ),
    ]
    fig.legend(
        handles=handles,
        frameon=False,
        fontsize=7.5,
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(0.45, -0.045),
    )
    save(fig, "fig4_agent_vs_model")


# ── figure 5: the new tests in detail ────────────────────────────────────────

NEW_TESTS = (
    ("exam_mygene2_hits.tsv", "MyGene2", "agent-v1.1", "Agent (v1.1)"),
    ("exam_cada-test_hits.tsv", "CADA test", "agent-v1.1", "Agent (v1.1)"),
    ("exam_casereports-exam_hits.tsv", "Case reports after the cutoff", "agent-v2", "Agent (v2)"),
)
SHOWN = {
    "llm-direct": ("Same model, asked directly", "model"),
    "one-way-merged": ("One-way similarity (no model)", "tool"),
    "rank-then-check": ("Rank, then check", "tool"),
    "lirical": ("LIRICAL", "tool"),
    "gpt-6.1": ("GPT-6.1, asked directly", "model"),
}
OMIM_ONLY = {
    "rank-then-check",
    "lirical",
}  # marked so on the case reports, where many diagnoses are not in OMIM


def fig5() -> None:
    present = [t for t in NEW_TESTS if (DOCS / t[0]).exists()]
    if not present:
        print("fig5: no test tables yet")
        return
    fig, axes = plt.subplots(
        len(present),
        1,
        figsize=(5.2, 1.85 * len(present) + 0.6),
        gridspec_kw={"hspace": 0.85},
        squeeze=False,
    )
    for ax, (name, title, agent, agent_label) in zip(axes[:, 0], present, strict=True):
        rows = hits_table(name)
        systems = [c.removesuffix("@1") for c in rows[0] if c.endswith("@1")]
        shown = [(agent_label, *count(rows, agent), "agent")]
        for s in SHOWN:
            if s in systems:
                label = SHOWN[s][0] + (
                    " (OMIM only)" if agent == "agent-v2" and s in OMIM_ONLY else ""
                )
                shown.append((label, *count(rows, s), SHOWN[s][1]))
        letter = "abc"[present.index((name, title, agent, agent_label))]
        interval_rows(ax, shown, xmax=70, title=f"{letter}   {title} (n = {len(rows)})")
    kind_legend(
        fig,
        ["agent", "model", "tool"],
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(0.5, -0.04),
        columnspacing=1.6,
    )
    save(fig, "fig5_new_tests")


# ── figure 6: by how many findings the patient has; by how rare the disease is ─


def fig6() -> None:
    import json

    bands = ["1–2", "3–5", "6–10", "11 or more"]

    def band(n: int) -> str:
        return bands[0] if n <= 2 else bands[1] if n <= 5 else bands[2] if n <= 10 else bands[3]

    findings: dict[str, int] = {}
    for folder in ("cada/56e42ec", "mygene2/6689035", "casereports/2026-10"):
        path = ROOT / "data" / "processed" / folder / "cases.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                case = json.loads(line)
                findings[case["id"]] = len(case["hpo_ids"])
    tables = [t for t in NEW_TESTS if (DOCS / t[0]).exists()]
    if not tables or not findings:
        print("fig6: no test tables yet")
        return
    fig, axes = plt.subplots(
        len(tables),
        1,
        figsize=(5.2, 2.3 * len(tables) + 0.6),
        gridspec_kw={"hspace": 0.75},
        squeeze=False,
    )
    for i, (ax, (name, title, agent, agent_label)) in enumerate(
        zip(axes[:, 0], tables, strict=True)
    ):
        rows_all = hits_table(name)
        rows = []
        for b in bands:
            inside = [r for r in rows_all if band(findings[r["case_id"]]) == b]
            if not inside:
                continue
            rows.append(
                (
                    f"{b} findings (n = {len(inside)})",
                    count(inside, agent),
                    count(inside, "llm-direct"),
                    pair_note(inside, agent, "llm-direct"),
                )
            )
        paired_rows(ax, rows, xmax=100)
        ax.set_title(
            f"{'abc'[i]}   {title} — {agent_label}", loc="left", fontsize=8.5, color=INK, pad=5
        )
        ax.text(
            100 * 1.02,
            len(rows) - 0.42,
            "agent : model, cases\nonly one gets right",
            fontsize=7.5,
            color=INK2,
            va="bottom",
            ha="left",
        )
    axes[-1, 0].set_xlabel("confirmed disease ranked first (%), with 95% interval")
    handles = [
        Line2D([0], [0], marker="o", ms=6, color=AGENT, lw=2, mec=SURFACE, mew=1.2, label="agent"),
        Line2D(
            [0],
            [0],
            marker="o",
            ms=6,
            color=MODEL,
            lw=2,
            mec=SURFACE,
            mew=1.2,
            label="the same model asked directly",
        ),
    ]
    fig.legend(
        handles=handles,
        frameon=False,
        fontsize=7.5,
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(0.45, -0.04),
    )
    save(fig, "fig6_by_findings")


FIGURES = {"fig1": fig1, "fig2": fig2, "fig3": fig3, "fig4": fig4, "fig5": fig5, "fig6": fig6}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(FIGURES):
        FIGURES[name]()

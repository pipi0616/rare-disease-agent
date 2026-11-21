"""Assemble the submission files from docs/paper: one manuscript with its references and
figures as a Word document, and the supplementary material as another.

    uv run python scripts/build_paper.py

Reads manuscript.md, references.md and supplementary.md; writes docs/paper/submission/.
It refuses to build while a placeholder ([[...]]) is left in the text.
"""

import re
import subprocess
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parents[1] / "docs" / "paper"
OUT = PAPER / "submission"
FIGURES = [
    ("fig1_design", "Fig. 1"),
    ("fig2_leakage", "Fig. 2"),
    ("fig3_heldout", "Fig. 3"),
    ("fig4_agent_vs_model", "Fig. 4"),
    ("fig5_new_tests", "Fig. 5"),
    ("fig6_by_findings", "Fig. 6"),
]


def references() -> str:
    """The numbered list of references.md, up to its notes for the authors."""
    text = (PAPER / "references.md").read_text(encoding="utf-8")
    listed = text.split("## To check by hand")[0]
    items = re.findall(r"^\d+\. .+$", listed, flags=re.M)
    return "\n".join(items)


def manuscript() -> str:
    text = (PAPER / "manuscript.md").read_text(encoding="utf-8")
    text = text.replace("[see `references.md`; inserted at conversion]", references())
    figures = ["## Figures", ""]
    for name, label in FIGURES:
        if (PAPER / "figures" / f"{name}.png").exists():
            figures += [f"![{label}](figures/{name}.png){{width=100%}}", "", f"*{label}*", ""]
    return text.rstrip() + "\n\n" + "\n".join(figures) + "\n"


def build(name: str, text: str, allow_placeholders: bool) -> None:
    left = re.findall(r"\[\[[^\]]+\]\]", text)
    if left and not allow_placeholders:
        sys.exit(f"{name}: {len(left)} placeholders left, e.g. {left[0][:60]}")
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / f"{name}.md"
    source.write_text(text, encoding="utf-8")
    subprocess.run(
        [
            "pandoc",
            str(source),
            "-o",
            str(OUT / f"{name}.docx"),
            "--from",
            "markdown",
            "--resource-path",
            str(PAPER),
            "--standalone",
        ],
        check=True,
    )
    words = len(re.findall(r"\w+", text))
    print(f"wrote {OUT / name}.docx  ({words:,} words, {len(left)} placeholders left)")


if __name__ == "__main__":
    draft = "--draft" in sys.argv
    build("manuscript", manuscript(), draft)
    build("supplementary", (PAPER / "supplementary.md").read_text(encoding="utf-8"), draft)

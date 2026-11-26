"""A test's results as tables, from the per-case verdicts `raredx eval hits` writes.

    systems   each system's first-place and top-ten rate with its 95% interval, and its
              paired comparison with the main system (cases each gets right alone, and
              the exact sign test)
    strata    the main system and one baseline by how many findings the patient has —
              a clinic's short lists against a case report's long ones

Several tests answer one question each (the agent against its own model asked
directly, on each test set): their p-values are corrected together by Holm's method.
"""

from collections.abc import Callable

from raredx.evals.scoring import p_value, rate, sign_test

Row = dict[str, str]  # one case of a hits table
BANDS = ((1, 2), (3, 5), (6, 10), (11, 10_000))  # findings per patient


def systems(rows: list[Row]) -> list[str]:
    """The systems of a hits table, in its column order."""
    return [c.removesuffix("@1") for c in rows[0] if c.endswith("@1")]


def paired(rows: list[Row], first: str, second: str, k: int = 1) -> tuple[int, int, float]:
    """Cases only the first system has in its top k, only the second, and the two-sided
    exact sign test's p."""
    a = sum(r[f"{first}@{k}"] == "1" and r[f"{second}@{k}"] != "1" for r in rows)
    b = sum(r[f"{second}@{k}"] == "1" and r[f"{first}@{k}"] != "1" for r in rows)
    return a, b, sign_test(a, b)


def holm(p_values: dict[str, float]) -> dict[str, float]:
    """Holm's step-down correction: the smallest p times the number of tests, the next
    times one fewer, and so on, never below the one before it, never above 1."""
    adjusted: dict[str, float] = {}
    worst = 0.0
    for i, (name, p) in enumerate(sorted(p_values.items(), key=lambda kv: kv[1])):
        worst = max(worst, min(1.0, p * (len(p_values) - i)))
        adjusted[name] = worst
    return adjusted


def _cell(hits: int, n: int) -> str:
    r = rate(hits, n)
    return f"{r.rate * 100:.1f}% [{r.low * 100:.1f}–{r.high * 100:.1f}]"


def systems_table(rows: list[Row], main: str) -> list[str]:
    """Markdown: one line per system, the main one first."""
    names = [main, *(s for s in systems(rows) if s != main)]
    lines = [
        f"| system (n = {len(rows)}) | top-1 | top-10 | paired at top-1, {main} : it | "
        "paired at top-10 |",
        "|---|---|---|---|---|",
    ]
    for name in names:
        cells = [_cell(sum(r[f"{name}@{k}"] == "1" for r in rows), len(rows)) for k in (1, 10)]
        versus = ["", ""]
        if name != main:
            for i, k in enumerate((1, 10)):
                won, lost, p = paired(rows, main, name, k)
                versus[i] = f"{won} : {lost} ({p_value(p)})"
        shown = f"**{name}**" if name == main else name
        lines.append(f"| {shown} | {cells[0]} | {cells[1]} | {versus[0]} | {versus[1]} |")
    return lines


def strata_table(
    rows: list[Row], group_of: Callable[[str], str], names: list[str], order: list[str]
) -> list[str]:
    """Markdown: first-place rate of each named system within each group of cases
    (`group_of`: case id -> group), in the given order of groups."""
    lines = [
        "| group | cases | " + " | ".join(names) + " |",
        "|---|---|" + "---|" * len(names),
    ]
    for group in order:
        inside = [r for r in rows if group_of(r["case_id"]) == group]
        if not inside:
            continue
        cells = [
            f"{sum(r[f'{name}@1'] == '1' for r in inside) / len(inside) * 100:.1f}%"
            for name in names
        ]
        lines.append(f"| {group} | {len(inside)} | " + " | ".join(cells) + " |")
    return lines


def findings_band(n: int) -> str:
    low, high = next(b for b in BANDS if b[0] <= n <= b[1])
    return f"{low}–{high} findings" if high < 10_000 else f"{low} or more findings"


FINDINGS_ORDER = [findings_band(low) for low, _ in BANDS]

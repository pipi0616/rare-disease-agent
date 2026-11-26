"""The test report's tables and the correction for several tests."""

import pytest

from raredx.evals import report


def rows() -> list[dict[str, str]]:
    def row(case: str, agent: tuple[int, int], direct: tuple[int, int]) -> dict[str, str]:
        return {
            "case_id": case,
            "pmid": "",
            "answerable": "1",
            "agent@1": str(agent[0]),
            "agent@10": str(agent[1]),
            "direct@1": str(direct[0]),
            "direct@10": str(direct[1]),
        }

    return [
        row("a", (1, 1), (0, 1)),
        row("b", (1, 1), (0, 0)),
        row("c", (1, 1), (1, 1)),
        row("d", (0, 1), (1, 1)),
        row("e", (0, 0), (0, 0)),
    ]


def test_pairs_count_what_each_system_alone_gets_right() -> None:
    assert report.systems(rows()) == ["agent", "direct"]
    won, lost, p = report.paired(rows(), "agent", "direct")
    assert (won, lost) == (2, 1) and p == pytest.approx(1.0)
    assert report.paired(rows(), "agent", "direct", k=10)[:2] == (1, 0)


def test_holm_multiplies_the_smallest_p_most_and_keeps_the_order() -> None:
    adjusted = report.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adjusted == pytest.approx({"a": 0.03, "c": 0.06, "b": 0.06})
    assert report.holm({"x": 0.6, "y": 0.9}) == pytest.approx({"x": 1.0, "y": 1.0})


def test_the_systems_table_puts_the_main_system_first_with_its_pairs() -> None:
    lines = report.systems_table(rows(), "agent")
    assert lines[2].startswith("| **agent** | 60.0% [")
    assert "2 : 1 (p = 1.000)" in lines[3] and "1 : 0" in lines[3]


def test_strata_split_the_cases_by_their_group() -> None:
    group = {"a": "1–2 findings", "b": "1–2 findings", "c": "3–5 findings"}
    lines = report.strata_table(
        rows(), lambda case: group.get(case, "other"), ["agent", "direct"], report.FINDINGS_ORDER
    )
    assert lines[2] == "| 1–2 findings | 2 | 100.0% | 0.0% |"
    assert lines[3] == "| 3–5 findings | 1 | 100.0% | 100.0% |"
    assert report.findings_band(4) == "3–5 findings"
    assert report.findings_band(40) == "11 or more findings"

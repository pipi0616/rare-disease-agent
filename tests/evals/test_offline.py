"""The offline evaluation's arithmetic: fusion, paired counts, the rule, coverage."""

from collections.abc import Sequence
from typing import Any

from raredx.evals import offline


def test_reciprocal_rank_fusion_favours_what_both_lists_rank_high() -> None:
    assert offline.rrf(["a", "b", "c"], ["b", "a", "d"])[:2] == ["a", "b"]
    assert offline.rrf(["a", "b"], ["c", "b"])[0] == "b"


def test_the_first_rank_looks_at_the_top_ten_only() -> None:
    ranked = [f"d{i}" for i in range(20)]
    assert offline.first_rank(ranked, {"d3"}) == 4
    assert offline.first_rank(ranked, {"d15"}) is None


def rows(
    config: tuple[str, str, str], source: str, ranks: Sequence[int | None]
) -> list[dict[str, Any]]:
    kb, ranker, order = config
    return [
        {
            "knowledge": kb,
            "ranker": ranker,
            "order": order,
            "source": source,
            "case_id": str(i),
            "rank": r,
        }
        for i, r in enumerate(ranks)
    ]


def test_a_configuration_passes_only_if_no_source_is_worse_and_two_are_better() -> None:
    new = ("merged", "O", "N")
    base = offline.BASELINE
    better, same = [1] * 12 + [None] * 4, [None] * 12 + [None] * 4
    data = (
        rows(base, "a", same)
        + rows(new, "a", better)
        + rows(base, "b", same)
        + rows(new, "b", better)
        + rows(base, "c", [1] * 16)
        + rows(new, "c", [1] * 16)
    )
    v = offline.verdict(data, new)
    assert v["pass"] and v["sources"]["a"][1][:2] == (12, 0)
    worse = data + rows(base, "d", [1] * 12 + [None] * 4) + rows(new, "d", [None] * 16)
    assert not offline.verdict(worse, new)["pass"]


def test_coverage_is_the_union_of_the_routes_and_none_when_a_route_is_missing() -> None:
    data = [
        {"lists": {"F": [], "M": []}, "hit": {"F": True, "M": False}},
        {"lists": {"F": [], "M": []}, "hit": {"F": False, "M": True}},
        {"lists": {"F": [], "M": []}, "hit": {"F": False, "M": False}},
    ]
    assert offline.coverage(data, "F") == 1 / 3
    assert offline.coverage(data, "M+F") == 2 / 3
    assert offline.coverage(data, "F+C") is None

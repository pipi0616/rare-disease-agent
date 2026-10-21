"""The scorer: weights learned on labelled rows, judged on other sources or other folds."""

import numpy as np

from raredx.ranking import model
from raredx.ranking.pool import Row

FEATURES = ("signal", "noise")


def rows(sources: tuple[str, ...] = ("a", "b", "c"), cases: int = 12) -> list[Row]:
    """Three candidates per case; the right one has the most signal, noise is random."""
    rng = np.random.default_rng(0)
    out = []
    for source in sources:
        for i in range(cases):
            case = f"{source}{i}"
            for j, signal in enumerate((0.9, 0.4, 0.1)):
                out.append(
                    Row(
                        source=source,
                        case_id=case,
                        disease_id=f"OMIM:{600000 + j}",
                        correct=j == 0,
                        features={"signal": signal + rng.normal(0, 0.05), "noise": rng.normal()},
                    )
                )
    return out


def test_the_learned_weights_put_the_right_candidate_first() -> None:
    data = rows()
    order = model.ranked(model.fit(data, FEATURES), data, FEATURES)
    assert all(ids[0] == "OMIM:600000" for ids in order.values()) and len(order) == 36


def test_the_weights_are_read_per_input_and_signal_counts_most() -> None:
    weights = model.weights(model.fit(rows(), FEATURES), FEATURES)
    assert list(weights) == ["signal", "noise", "signal vs best", "noise vs best"]
    assert max(weights, key=lambda f: abs(weights[f])).startswith("signal")


def test_other_sources_ranks_every_case_by_weights_learned_elsewhere() -> None:
    data = rows()
    order = model.other_sources(data, FEATURES)
    assert set(order) == {r.case_id for r in data}
    assert sum(ids[0] == "OMIM:600000" for ids in order.values()) == 36


def test_same_source_ranks_every_case_by_its_own_sources_other_folds() -> None:
    data = rows(sources=("a",), cases=10)
    order = model.same_source(data, FEATURES)
    assert set(order) == {r.case_id for r in data}


def test_each_source_weighs_the_same_whatever_its_size() -> None:
    # A large source where noise decides, a small one where signal does: weighed by rows,
    # the large one would set the weights alone.
    big = rows(sources=("big",), cases=40)
    for r in big:
        r.features["noise"] = 1.0 if r.correct else 0.0
    small = rows(sources=("small",), cases=4)
    weights = model.weights(model.fit(big + small, FEATURES), FEATURES)
    assert weights["signal"] > 0 and weights["noise"] > 0

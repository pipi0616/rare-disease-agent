"""The mask: set for one case, invisible to every other."""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from raredx.knowledge import masking


def test_nothing_is_masked_outside_evaluation() -> None:
    assert masking.current() == frozenset()


def test_a_mask_holds_inside_its_block_only_even_after_an_error() -> None:
    with masking.masked(["PMID:1"]):
        assert masking.current() == {"PMID:1"}
        with masking.masked(["PMID:2"]):
            assert masking.current() == {"PMID:2"}
        assert masking.current() == {"PMID:1"}
    with pytest.raises(RuntimeError), masking.masked(["PMID:3"]):
        raise RuntimeError
    assert masking.current() == frozenset()


def test_cases_answered_in_parallel_threads_each_see_only_their_own_mask() -> None:
    def answer(paper: str) -> frozenset[str]:
        with masking.masked([paper]):
            time.sleep(0.01)  # let the threads overlap
            return masking.current()

    papers = [f"PMID:{i}" for i in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        seen = list(pool.map(answer, papers))
    assert seen == [frozenset({p}) for p in papers]

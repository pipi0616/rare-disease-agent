"""What model calls cost: counted per request, and capped per run."""

from types import SimpleNamespace
from typing import Any

import pytest

from raredx.config import Settings
from raredx.llm import Budget, BudgetExceeded, Tally


def response(**usage: Any) -> Any:
    return SimpleNamespace(usage=SimpleNamespace(**usage))


def test_a_tally_reads_cached_tokens_whichever_way_the_provider_reports_them() -> None:
    tally = Tally()
    tally.add(response(prompt_tokens=100, completion_tokens=10, prompt_cache_hit_tokens=40))
    details = SimpleNamespace(cached_tokens=5)  # OpenAI's way
    tally.add(response(prompt_tokens=50, completion_tokens=5, prompt_tokens_details=details))
    tally.add(SimpleNamespace())  # no usage reported: not counted
    assert (tally.model_calls, tally.input_tokens, tally.cached_input_tokens) == (2, 150, 45)
    assert tally.output_tokens == 15
    prices = Settings(llm_price_input=1.0, llm_price_cached_input=0.5, llm_price_output=2.0)
    assert tally.cost(prices) == pytest.approx((105 * 1.0 + 45 * 0.5 + 15 * 2.0) / 1e6)


def test_a_budget_estimates_a_call_the_provider_did_not_price() -> None:
    budget = Budget(0.001, prices=(1.0, 0.0, 10.0))  # USD per million tokens
    budget.charge(response(prompt_tokens=500, completion_tokens=40, prompt_cache_hit_tokens=0))
    assert budget.spent == pytest.approx(0.0009)
    budget.check()  # under the cap
    budget.charge(response(prompt_tokens=100, completion_tokens=0, prompt_cache_hit_tokens=0))
    with pytest.raises(BudgetExceeded):
        budget.check()


def test_a_budget_takes_the_providers_own_price_when_given() -> None:
    budget = Budget(1.0, prices=(1.0, 0.0, 10.0))
    budget.charge(response(prompt_tokens=10**6, completion_tokens=0, cost=0.02))
    assert budget.spent == pytest.approx(0.02)

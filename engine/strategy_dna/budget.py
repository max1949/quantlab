"""Bounded autonomous research budget (QLN-6)."""

from __future__ import annotations

from pydantic import BaseModel

from engine.strategies.v2.errors import SpecV2Error


class ResearchBudget(BaseModel):
    max_new_candidates: int = 5
    max_counterfactuals_per_strategy: int = 3
    allow_ai_generation: bool = True
    require_negative_result_logging: bool = True
    optimize_until_pass: bool = False  # hard deny conceptually


def assert_within_budget(budget: ResearchBudget, *, created: int) -> None:
    if budget.optimize_until_pass:
        raise SpecV2Error("OPTIMIZE_UNTIL_PASS is forbidden")
    if created > budget.max_new_candidates:
        raise SpecV2Error(
            f"research budget exceeded: created={created} > max={budget.max_new_candidates}"
        )

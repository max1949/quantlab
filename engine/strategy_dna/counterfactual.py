"""Counterfactual Lab — bounded what-if diffs without rewriting history."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from engine.strategy_dna.budget import ResearchBudget, assert_within_budget
from engine.strategy_dna.dna import StrategyDNA


class CounterfactualRequest(BaseModel):
    base_strategy_id: str
    change_description: str
    changed_params: dict[str, Any] = Field(default_factory=dict)
    must_not_optimize_until_pass: bool = True


class CounterfactualResult(BaseModel):
    base_strategy_id: str
    status: str  # RECORDED | DENIED
    notes: str = ""
    changed_params: dict[str, Any] = Field(default_factory=dict)


def propose_counterfactual(
    dna: StrategyDNA,
    req: CounterfactualRequest,
    *,
    budget: ResearchBudget,
    already_run: int,
) -> CounterfactualResult:
    assert_within_budget(budget, created=already_run + 1)
    if not req.must_not_optimize_until_pass:
        return CounterfactualResult(
            base_strategy_id=dna.strategy_id,
            status="DENIED",
            notes="counterfactual must keep must_not_optimize_until_pass=true",
        )
    if already_run >= budget.max_counterfactuals_per_strategy:
        return CounterfactualResult(
            base_strategy_id=dna.strategy_id,
            status="DENIED",
            notes="counterfactual budget exhausted for strategy",
        )
    return CounterfactualResult(
        base_strategy_id=dna.strategy_id,
        status="RECORDED",
        notes=req.change_description,
        changed_params=dict(req.changed_params),
    )

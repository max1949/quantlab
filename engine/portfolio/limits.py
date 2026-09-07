"""Portfolio limits — capital / instrument / drawdown / crowding budgets."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PortfolioLimits(BaseModel):
    max_strategies: int = 10
    max_gross_exposure: float = 1.0
    max_net_exposure: float = 1.0
    max_per_instrument_weight: float = 0.5
    max_per_strategy_weight: float = 0.5
    max_drawdown_budget: float = 0.25
    max_pairwise_correlation: float = 0.85
    max_cluster_size: int = 3
    forbid_bypass_invariants: bool = True
    real_money: bool = False  # hard deny conceptually

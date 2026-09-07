"""QLN-7 Portfolio Governor tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.portfolio import (
    PortfolioGovernor,
    PortfolioLimits,
    evaluate_portfolio,
    pairwise_return_correlation,
)


def _rets(seed: int, n: int = 80) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="B", tz="UTC")
    return pd.Series(rng.normal(0, 0.01, size=n), index=idx)


def test_allow_within_limits():
    gov = PortfolioGovernor(
        strategy_ids=["hist_fl_momentum_w20", "hist_fl_rsi_w14"],
        weights={"hist_fl_momentum_w20": 0.4, "hist_fl_rsi_w14": 0.4},
        instruments={"hist_fl_momentum_w20": "RB", "hist_fl_rsi_w14": "AU"},
        drawdowns={"hist_fl_momentum_w20": -0.05, "hist_fl_rsi_w14": -0.04},
        limits=PortfolioLimits(),
    )
    actions = evaluate_portfolio(
        gov,
        returns={
            "hist_fl_momentum_w20": _rets(1),
            "hist_fl_rsi_w14": _rets(2),
        },
    )
    assert any(a.kind == "ALLOW" for a in actions)
    assert all(a.bypasses_invariants is False for a in actions)
    assert all(a.auditable and a.replayable for a in actions)


def test_correlation_block():
    base = _rets(7)
    noisy = base + _rets(8) * 0.01
    corr = pairwise_return_correlation({"a": base, "b": noisy})
    assert corr["max_abs"] > 0.8
    gov = PortfolioGovernor(
        strategy_ids=["a", "b"],
        weights={"a": 0.3, "b": 0.3},
        limits=PortfolioLimits(max_pairwise_correlation=0.5),
    )
    actions = evaluate_portfolio(gov, returns={"a": base, "b": noisy})
    assert any(a.kind == "BLOCK_ADD" for a in actions)


def test_deny_real_money_flag():
    gov = PortfolioGovernor(
        strategy_ids=["x"],
        weights={"x": 0.1},
        limits=PortfolioLimits(real_money=True),
    )
    actions = evaluate_portfolio(gov)
    assert any(a.kind == "DENY_REAL_MONEY" for a in actions)


def test_weight_and_drawdown_derisk():
    gov = PortfolioGovernor(
        strategy_ids=["heavy"],
        weights={"heavy": 0.9},
        drawdowns={"heavy": -0.4},
        limits=PortfolioLimits(max_per_strategy_weight=0.5, max_drawdown_budget=0.25),
    )
    actions = evaluate_portfolio(gov)
    kinds = {a.kind for a in actions}
    assert "REDUCE_WEIGHT" in kinds
    assert "DE_RISK" in kinds

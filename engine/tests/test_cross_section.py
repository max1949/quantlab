"""截面回测指标测试。"""

import numpy as np
import pandas as pd

from engine.cross_section import run_cross_section_backtest
from engine.cost_model import CostConfig


def _make_panel(n: int = 120, seed: int = 7) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-03", periods=n, freq="B")
    signals = {}
    closes = {}
    for sym, bias in (("RB", 0.02), ("AU", -0.01)):
        close = 100 * np.cumprod(1 + rng.normal(0.001 + bias, 0.02, n))
        signals[sym] = pd.Series(rng.normal(bias, 1, n), index=idx)
        closes[sym] = pd.Series(close, index=idx)
    return signals, closes


def test_cross_section_backtest_runs():
    signals, closes = _make_panel()
    out = run_cross_section_backtest(signals, closes, top_n=1, long_short=True)
    assert out["metrics"]["periods"] > 0
    assert out["metrics"]["sharpe"] is not None
    assert len(out["equity_curve"]) > 0


def test_cross_section_negative_equity_no_500():
    """净值穿零时不应因复数年化抛 TypeError。"""
    signals, closes = _make_panel(n=80, seed=99)
    out = run_cross_section_backtest(
        signals,
        closes,
        cost_config=CostConfig(fee_rate=0.05, slippage_bps=500.0),
        top_n=1,
        long_short=True,
    )
    assert out["metrics"]["annual_return"] is not None or out["metrics"]["total_return"] is not None

"""engine 回测/成本/报告纯函数测试。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.backtest import run_backtest, signal_to_positions
from engine.cost_model import CostConfig, apply_costs, turnover
from engine.report import build_research_report
from engine.factor_engine import compute_template_factor, sample_price_frame


@pytest.fixture()
def ohlcv() -> pd.DataFrame:
    return sample_price_frame(n=252, seed=11)


def test_turnover_first_period_is_initial_position():
    pos = pd.Series([1.0, 1.0, -1.0, 0.0])
    t = turnover(pos)
    assert t.iloc[0] == 1.0  # 建仓
    assert t.iloc[1] == 0.0  # 不变
    assert t.iloc[2] == 2.0  # 多->空
    assert t.iloc[3] == 1.0  # 空->平


def test_apply_costs_scales_with_turnover():
    pos = pd.Series([1.0, 1.0, -1.0])
    cfg = CostConfig(fee_rate=0.001, slippage_bps=10.0)  # per_turnover = 0.001+0.001=0.002
    costs = apply_costs(pos, cfg)
    assert costs.iloc[0] == pytest.approx(0.002)
    assert costs.iloc[1] == pytest.approx(0.0)
    assert costs.iloc[2] == pytest.approx(0.004)


def test_signal_to_positions_sign():
    s = pd.Series([0.5, -0.3, 0.0, np.nan])
    p = signal_to_positions(s)
    assert list(p) == [1.0, -1.0, 0.0, 0.0]


def test_run_backtest_structure_and_keys(ohlcv):
    signal = compute_template_factor(ohlcv, "momentum", {"window": 10})
    result = run_backtest(signal, ohlcv, CostConfig())
    m = result["metrics"]
    assert set(m) >= {
        "total_return", "annual_return", "annual_volatility", "sharpe",
        "max_drawdown", "win_rate", "trade_count", "turnover", "periods",
    }
    assert m["periods"] == 252
    assert len(result["equity_curve"]) == 252
    assert result["equity_curve"][0]["equity"] is not None


def test_costs_reduce_returns(ohlcv):
    signal = compute_template_factor(ohlcv, "momentum", {"window": 5})
    free = run_backtest(signal, ohlcv, CostConfig(fee_rate=0.0, slippage_bps=0.0))
    costly = run_backtest(signal, ohlcv, CostConfig(fee_rate=0.01, slippage_bps=50.0))
    assert costly["metrics"]["total_return"] < free["metrics"]["total_return"]


def test_zero_signal_means_flat(ohlcv):
    flat = pd.Series(0.0, index=ohlcv.index)
    result = run_backtest(flat, ohlcv, CostConfig())
    assert result["metrics"]["trade_count"] == 0
    assert result["metrics"]["total_return"] == pytest.approx(0.0, abs=1e-9)


def test_run_backtest_missing_close_raises():
    bad = pd.DataFrame({"volume": [1, 2, 3]})
    with pytest.raises(ValueError):
        run_backtest(pd.Series([1, 1, 1]), bad)


def test_build_research_report_sections():
    metrics = {
        "total_return": 0.2, "annual_return": 0.2, "annual_volatility": 0.15,
        "sharpe": 1.3, "max_drawdown": -0.1, "win_rate": 0.55,
        "trade_count": 20, "turnover": 30.0, "periods": 252,
    }
    report = build_research_report(
        factor_name="动量10", factor_kind="template", factor_spec={"params": {"window": 10}},
        symbol="RB", cost_config={"fee_rate": 0.0005, "slippage_bps": 1.0},
        metrics=metrics,
        snapshot={"symbol": "RB", "start_date": "2024-01-01", "end_date": "2024-12-31",
                  "rows": 252, "content_hash": "abc123"},
    )
    assert set(report) >= {"hypothesis", "method", "results", "conclusion", "grade", "markdown"}
    assert report["grade"] == "良好"  # sharpe 1.3
    assert "研究报告" in report["markdown"]
    assert "abc123" in report["markdown"]  # 快照可复现信息


def test_report_grade_for_negative_sharpe():
    report = build_research_report(
        factor_name="x", factor_kind="template", factor_spec={},
        symbol="AU", cost_config={"fee_rate": 0, "slippage_bps": 0},
        metrics={"sharpe": -0.5, "max_drawdown": -0.3},
    )
    assert report["grade"] == "无效"

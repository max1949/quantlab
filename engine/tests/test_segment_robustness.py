"""日盘/夜盘分段与容量提示测试。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.segment_robustness import (
    evaluate_session_segments,
    turnover_capacity_hint,
)
from engine.factor_engine import compute_template_factor, sample_price_frame


def _intraday_ohlcv(n: int = 6000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    idx = pd.date_range("2024-01-02 09:00", periods=n, freq="5min")
    close = 100 * np.cumprod(1 + rng.normal(0, 0.001, n))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) + 0.1
    low = np.minimum(open_, close) - 0.1
    volume = rng.integers(100, 5000, size=n)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )


def _signal_fn(df):
    return compute_template_factor(df, "momentum", {"window": 20})


def test_session_segments_on_intraday():
    df = _intraday_ohlcv()
    out = evaluate_session_segments(_signal_fn, df, timeframe="5m")
    assert out["skipped"] is False
    assert len(out["segments"]) == 2
    assert out["summary"]["n_active"] >= 1


def test_session_skipped_on_daily():
    df = sample_price_frame(200)
    out = evaluate_session_segments(_signal_fn, df, timeframe="1d")
    assert out["skipped"] is True


def test_turnover_capacity_hint():
    assert turnover_capacity_hint(10.0, "1d") is None
    assert turnover_capacity_hint(50.0, "5m") is not None
    assert turnover_capacity_hint(90.0, "1d") is not None

"""行情数据质量闸门测试。"""

from __future__ import annotations

import pandas as pd

from engine.data_quality import assess_ohlcv_quality
from engine.factor_engine import sample_price_frame


def test_sample_daily_data_passes():
    df = sample_price_frame(300)
    q = assess_ohlcv_quality(df, "1d")
    assert q["stats"]["rows"] == 300
    assert q["passed"] is True
    assert q["grade"] == "良好"


def test_detects_large_gaps_and_limit_locks():
    idx = pd.date_range("2024-01-02", periods=100, freq="B")
    df = sample_price_frame(100)
    df.index = idx
    # 人为插入大缺口
    df2 = pd.concat([df.iloc[:40], df.iloc[55:]])
    q = assess_ohlcv_quality(df2, "1d")
    assert q["stats"]["large_gap_count"] >= 1

    flat = df.copy()
    flat["high"] = flat["close"]
    flat["low"] = flat["close"]
    flat["open"] = flat["close"]
    flat.loc[flat.index[10:30], "volume"] = 0
    q2 = assess_ohlcv_quality(flat, "1d")
    assert q2["stats"]["limit_lock_bars"] >= 10
    assert any("涨跌停" in w or "零成交" in w for w in q2["warnings"])

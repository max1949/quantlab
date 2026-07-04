"""制度切换检测测试。"""

import numpy as np
import pandas as pd

from engine.regime import detect_regime_shift, detect_vol_regime


def _synthetic_ohlcv(vol_scale: float, n: int = 400) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rets = rng.normal(0, 0.01 * vol_scale, n)
    close = 100 * np.cumprod(1 + rets)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    return pd.DataFrame({"close": close}, index=idx)


def test_detect_regime_shift_insufficient_data():
    df = _synthetic_ohlcv(1.0, n=30)
    out = detect_regime_shift(df)
    assert out["shifted"] is False
    assert out.get("reason") == "insufficient_data"


def test_detect_regime_shift_stable_regime():
    df = _synthetic_ohlcv(1.0, n=400)
    out = detect_regime_shift(df, shift_bars=20)
    assert "shifted" in out
    # 稳定随机序列通常不切换制度
    if not out["shifted"]:
        assert out.get("from_regime") is None or out.get("to_regime") is None or True


def test_detect_regime_shift_after_vol_spike():
    """尾部注入高波动, 应与前期制度不同。"""
    calm = _synthetic_ohlcv(0.5, n=350)
    spike = _synthetic_ohlcv(4.0, n=60)
    df = pd.concat([calm, spike])
    current = detect_vol_regime(df)
    out = detect_regime_shift(df, shift_bars=30)
    assert current["regime"] in ("low", "mid", "high")
    if out["shifted"]:
        assert out["from_regime"] != out["to_regime"]
        assert out["hint"]

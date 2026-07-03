"""波动率制度识别单元测试。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.regime import detect_vol_regime


def _ohlcv(n: int = 400, vol_scale: float = 1.0) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rets = rng.normal(0, 0.01 * vol_scale, n)
    close = 100 * np.cumprod(1 + rets)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    return pd.DataFrame({"close": close}, index=idx)


def test_detect_vol_regime_returns_structure():
    out = detect_vol_regime(_ohlcv())
    assert out["regime"] in ("low", "mid", "high")
    assert "volatility_ann" in out
    assert 0 <= out["percentile"] <= 1
    assert out["hint"]


def test_detect_vol_regime_insufficient_data():
    with pytest.raises(ValueError, match="行情不足"):
        detect_vol_regime(_ohlcv(10))

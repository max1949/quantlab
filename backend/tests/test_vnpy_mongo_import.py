"""vn.py Mongo 导入工具测试 (不依赖真实 MongoDB)。"""

import pandas as pd

from backend.app.services.vnpy_mongo_import import MONGO_SYMBOL_MAP, resample_ohlcv


def test_symbol_map_rb_ag():
    assert MONGO_SYMBOL_MAP["RB888"] == "RB"
    assert MONGO_SYMBOL_MAP["AG888"] == "AU"


def test_resample_ohlcv_daily():
    idx = pd.date_range("2024-01-02 09:00", periods=120, freq="1min")
    df = pd.DataFrame(
        {
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 10,
            "open_interest": 5000,
        },
        index=idx,
    )
    daily = resample_ohlcv(df, "1D")
    assert len(daily) >= 1
    assert "open_interest" in daily.columns

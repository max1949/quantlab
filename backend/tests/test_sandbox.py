"""沙箱 AST 校验与执行测试。"""

import pandas as pd
import pytest

from sandbox.ast_guard import validate_source
from sandbox.runner import SandboxError, run_user_factor


GOOD_SOURCE = """
def compute(ohlcv):
    close = ohlcv["close"]
    return (close - close.rolling(5).mean()) / close.rolling(5).std()
"""


def test_validate_source_accepts_compute():
    ok, errs = validate_source(GOOD_SOURCE)
    assert ok, errs


def test_validate_source_rejects_import():
    ok, errs = validate_source("import os\ndef compute(ohlcv):\n    return ohlcv['close']")
    assert not ok
    assert any("Import" in e or "不允许" in e for e in errs)


def test_validate_source_requires_compute():
    ok, errs = validate_source("x = 1")
    assert not ok
    assert any("compute" in e for e in errs)


def test_run_user_factor_returns_series():
    idx = pd.date_range("2024-01-02", periods=60, freq="D")
    df = pd.DataFrame(
        {
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0 + pd.Series(range(60)).values * 0.1,
            "volume": 1000,
        },
        index=idx,
    )
    series = run_user_factor(GOOD_SOURCE, df)
    assert len(series) == len(df)
    assert series.notna().any()


def test_run_user_factor_rejects_eval():
    bad = """
def compute(ohlcv):
    return eval("ohlcv['close']")
"""
    idx = pd.date_range("2024-01-02", periods=10, freq="D")
    df = pd.DataFrame(
        {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 1},
        index=idx,
    )
    with pytest.raises(SandboxError):
        run_user_factor(bad, df)

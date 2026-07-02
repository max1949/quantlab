"""Python 快评引擎测试。"""

from __future__ import annotations

from engine.factor_engine import sample_price_frame
from engine.python_eval import evaluate_python_source

GOOD = """
def compute(ohlcv):
    close = ohlcv["close"]
    return close.pct_change(5)
"""


def test_evaluate_python_source_returns_metrics():
    df = sample_price_frame(400)
    result = evaluate_python_source(df, GOOD)
    assert result.get("source")
    assert "coach_summary" in result
    assert isinstance(result.get("publish_hints"), list)


def test_evaluate_python_rejects_bad_source():
    df = sample_price_frame(200)
    try:
        evaluate_python_source(df, "import os")
        assert False, "should raise"
    except Exception:
        pass

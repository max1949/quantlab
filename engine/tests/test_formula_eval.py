"""公式快评引擎测试。"""

from __future__ import annotations

from engine.factor_engine import sample_price_frame
from engine.formula_eval import evaluate_formula


def test_evaluate_formula_returns_metrics():
    df = sample_price_frame(400)
    expr = "mom(close, 20)"
    result = evaluate_formula(df, expr)
    assert result["expr"] == expr
    assert result.get("score") is not None or result.get("sharpe") is not None
    assert "coach_summary" in result
    assert isinstance(result.get("publish_hints"), list)


def test_evaluate_formula_rejects_bad_expr():
    df = sample_price_frame(200)
    try:
        evaluate_formula(df, "import os")
        assert False, "should raise"
    except Exception:
        pass

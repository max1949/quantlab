"""模板快评引擎测试。"""

from __future__ import annotations

from engine.factor_engine import sample_price_frame
from engine.template_eval import evaluate_template


def test_evaluate_template_returns_metrics():
    df = sample_price_frame(400)
    result = evaluate_template(df, "momentum", {"window": 20})
    assert result["template_type"] == "momentum"
    assert result["params"]["window"] == 20
    assert "coach_summary" in result
    assert isinstance(result.get("publish_hints"), list)

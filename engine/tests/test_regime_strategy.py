"""制度 × 策略适配测试。"""

from engine.regime_strategy import infer_strategy_style, score_regime_fit


def test_infer_from_template_type():
    assert infer_strategy_style(template_type="momentum") == "trend"
    assert infer_strategy_style(template_type="mean_reversion") == "mean_reversion"


def test_score_regime_fit_high_vol_mean_reversion():
    out = score_regime_fit("high", "mean_reversion")
    assert out["fit_score"] >= 75
    assert out["fit_verdict"] == "适合"


def test_score_regime_fit_high_vol_trend_caution():
    out = score_regime_fit("high", "trend")
    assert out["fit_score"] < 55
    assert out["fit_verdict"] == "谨慎"

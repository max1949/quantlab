"""研究质量闸门测试。"""

from engine.research_quality import QualityThresholds, assess_publish_readiness


def test_publish_gate_passes_strong_factor():
    verdict = assess_publish_readiness(
        backtest_metrics={"sharpe": 1.2},
        validation_status="success",
        validation_oos={"out_of_sample": {"sharpe": 0.8}},
        validation_robustness={
            "score": 55,
            "grade": "中等",
            "sealed_holdout": {"metrics": {"sharpe": 0.3}},
        },
    )
    assert verdict.passed is True


def test_publish_gate_blocks_weak_oos():
    verdict = assess_publish_readiness(
        backtest_metrics={"sharpe": 1.5},
        validation_status="success",
        validation_oos={"out_of_sample": {"sharpe": -0.2}},
        validation_robustness={"score": 60, "grade": "中等", "sealed_holdout": {"metrics": {"sharpe": 0.1}}},
        thresholds=QualityThresholds(min_oos_sharpe=0.0),
    )
    assert verdict.passed is False
    assert any("样本外" in r for r in verdict.reasons)

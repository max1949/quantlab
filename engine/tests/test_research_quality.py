"""研究质量闸门测试。"""

from engine.research_quality import (
    PaperThresholds,
    QualityThresholds,
    assess_paper_readiness,
    assess_publish_readiness,
)
from engine.validation.decision import MIN_PERIODS_FOR_EVIDENCE, MIN_TRADE_COUNT_FOR_EVIDENCE


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


def test_publish_gate_blocks_high_turnover():
    verdict = assess_publish_readiness(
        backtest_metrics={"sharpe": 1.2, "turnover": 95.0},
        validation_status="success",
        validation_oos={"out_of_sample": {"sharpe": 0.8}},
        validation_robustness={
            "score": 55,
            "grade": "中等",
            "sealed_holdout": {"metrics": {"sharpe": 0.3}},
        },
        thresholds=QualityThresholds(max_turnover=80.0),
    )
    assert verdict.passed is False
    assert any("换手" in r for r in verdict.reasons)


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


def test_paper_gate_blocks_one_trade_huge_sharpe():
    verdict = assess_paper_readiness(
        backtest_metrics={"sharpe": 99.0, "trade_count": 1, "periods": 40, "turnover": 5.0},
        validation_status="success",
        validation_oos={"out_of_sample": {"sharpe": 40.0}},
        validation_robustness={
            "score": 90.0,
            "grade": "稳健",
            "sealed_holdout": {"metrics": {"sharpe": 1.0}},
            "factor_ic": {"ic_mean": 0.05},
        },
        regime_fit_score=80,
        thresholds=PaperThresholds(),
    )
    assert verdict.passed is False
    assert any("证据线" in r for r in verdict.reasons)


def test_paper_gate_passes_with_evidence_floors():
    verdict = assess_paper_readiness(
        backtest_metrics={
            "sharpe": 0.5,
            "trade_count": MIN_TRADE_COUNT_FOR_EVIDENCE,
            "periods": MIN_PERIODS_FOR_EVIDENCE,
            "turnover": 20.0,
        },
        validation_status="success",
        validation_oos={"out_of_sample": {"sharpe": 0.4}},
        validation_robustness={
            "score": 60.0,
            "grade": "中等",
            "sealed_holdout": {"metrics": {"sharpe": 0.1}},
            "factor_ic": {"ic_mean": 0.03},
        },
        regime_fit_score=40,
        thresholds=PaperThresholds(),
    )
    assert verdict.passed is True

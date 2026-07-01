"""纸面衰减评估测试。"""

from engine.paper_decay import assess_paper_decay


def test_decay_ok_when_stable():
    v = assess_paper_decay(
        validation_oos={"out_of_sample": {"sharpe_ratio": 1.0, "max_drawdown": -0.1}},
        paper_metrics={"sharpe": 0.9, "max_drawdown": -0.11},
        nav_series=[1.0, 1.02, 1.01],
    )
    assert v.status == "ok"


def test_decay_alert_on_sharpe_drop():
    v = assess_paper_decay(
        validation_oos={"out_of_sample": {"sharpe": 1.2, "max_drawdown": -0.08}},
        paper_metrics={"sharpe": 0.5, "max_drawdown": -0.2},
        nav_series=[1.0, 0.92, 0.88],
    )
    assert v.status == "alert"
    assert v.reasons

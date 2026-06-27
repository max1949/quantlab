"""engine.research_report 纯函数测试。"""

from __future__ import annotations

from engine.research_report import build_project_report


def _factor(name="mom20", tt="momentum", window=20, kind="template"):
    return {"name": name, "kind": kind, "template_type": tt, "spec": {"params": {"window": window}}}


def _validation(is_s, oos_s, grade, wf_pos=0.6, notes=None):
    return {
        "oos": {
            "in_sample": {"sharpe": is_s},
            "out_of_sample": {"sharpe": oos_s, "max_drawdown": -0.1},
            "sharpe_degradation": is_s - oos_s,
        },
        "walk_forward": {"summary": {"positive_ratio": wf_pos}},
        "robustness": {"score": 60 if grade == "中等" else 20, "grade": grade, "notes": notes or []},
    }


def test_title_and_hypothesis_for_momentum():
    r = build_project_report(factor=_factor(), symbol="RB")
    assert "20日" in r["title"] and "动量" in r["title"] and "RB" in r["title"]
    assert "延续" in r["hypothesis"]
    assert r["stages"] == {"factor": True, "backtest": False, "validation": False}


def test_weak_validation_marks_overfit_in_results():
    r = build_project_report(
        factor=_factor(),
        symbol="RB",
        validation=_validation(1.2, -0.7, "脆弱", wf_pos=0.25, notes=["样本外夏普非正, 警惕过拟合。"]),
    )
    assert any("过拟合" in x for x in r["result_summary"])
    assert any("过拟合" in x for x in r["risks"])
    assert any("一致性" in x for x in r["risks"])
    assert r["grade"] == "脆弱"
    assert "# RB" in r["markdown"]


def test_strong_validation_recommends_competition():
    r = build_project_report(
        factor=_factor(),
        symbol="RB",
        backtest_metrics={"annual_return": 0.3, "sharpe": 1.6, "max_drawdown": -0.1, "win_rate": 0.6, "turnover": 2.0},
        validation=_validation(1.5, 1.3, "稳健", wf_pos=0.8),
    )
    assert any("赛季" in x or "跨品种" in x for x in r["next_steps"])
    assert r["stages"]["backtest"] and r["stages"]["validation"]


def test_ai_suggestions_override_next_steps():
    r = build_project_report(
        factor=_factor(),
        symbol="RB",
        validation=_validation(0.2, 0.1, "偏弱"),
        ai_suggestions=["AI: 增加波动率过滤", "AI: 扩大样本"],
    )
    assert r["next_steps"][0].startswith("AI:")


def test_high_drawdown_and_turnover_flagged():
    r = build_project_report(
        factor=_factor(),
        symbol="RB",
        backtest_metrics={"annual_return": 0.5, "sharpe": 0.4, "max_drawdown": -0.45, "win_rate": 0.4, "turnover": 9.0},
    )
    joined = " ".join(r["risks"])
    assert "回撤" in joined and "换手" in joined


def test_deterministic():
    f = _factor()
    v = _validation(0.9, 0.3, "中等")
    assert build_project_report(factor=f, symbol="RB", validation=v) == build_project_report(
        factor=f, symbol="RB", validation=v
    )

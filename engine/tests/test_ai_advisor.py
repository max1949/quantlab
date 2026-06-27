"""engine.ai_advisor 纯函数测试 (确定性, 无网络)。"""

from __future__ import annotations

from engine.ai_advisor import (
    DISCLAIMER,
    MENTOR_SYSTEM,
    build_backtest_summary_prompt,
    build_research_plan_prompt,
    build_validation_review_prompt,
    local_backtest_summary,
    local_research_plan,
    local_validation_review,
)


def _val_ctx(oos_sharpe, is_sharpe, wf_pos, sens_pos, score, grade):
    return {
        "factor": {"name": "mom20", "kind": "template", "template_type": "momentum"},
        "symbol": "RB",
        "oos": {
            "in_sample": {"sharpe": is_sharpe},
            "out_of_sample": {"sharpe": oos_sharpe, "max_drawdown": -0.1},
            "sharpe_degradation": (is_sharpe - oos_sharpe),
        },
        "walk_forward": {"summary": {"positive_ratio": wf_pos}},
        "sensitivity": {"summary": {"positive_ratio": sens_pos, "n_variants": 3}},
        "robustness": {"score": score, "grade": grade},
    }


def test_review_weak_factor_flags_overfit():
    ctx = _val_ctx(oos_sharpe=-0.7, is_sharpe=1.2, wf_pos=0.25, sens_pos=0.3, score=23.8, grade="脆弱")
    r = local_validation_review(ctx)
    joined = " ".join(r["risks"])
    assert "过拟合" in joined
    assert any("衰减" in x for x in r["risks"])
    assert r["suggestions"]  # 必给改进建议
    assert "脆弱" in r["verdict"]
    assert r["markdown"].startswith("**结论**")


def test_review_strong_factor_has_strengths():
    ctx = _val_ctx(oos_sharpe=1.4, is_sharpe=1.5, wf_pos=0.8, sens_pos=0.75, score=82.0, grade="稳健")
    r = local_validation_review(ctx)
    assert r["strengths"]
    assert any("跨品种" in s or "竞赛" in s or "赛季" in s for s in r["suggestions"])
    assert "稳健" in r["verdict"]


def test_review_is_deterministic():
    ctx = _val_ctx(0.2, 0.9, 0.4, 0.4, 40.0, "偏弱")
    assert local_validation_review(ctx) == local_validation_review(ctx)


def test_validation_prompt_shape():
    ctx = _val_ctx(0.2, 0.9, 0.4, 0.4, 40.0, "偏弱")
    p = build_validation_review_prompt(ctx)
    assert p["system"] == MENTOR_SYSTEM
    assert "改进建议" in p["user"]
    assert "RB" in p["user"]


def test_backtest_summary_flags_risk():
    ctx = {
        "factor": {"name": "f1", "kind": "template"},
        "symbol": "RB",
        "metrics": {
            "annual_return": 0.3,
            "sharpe": 0.2,
            "max_drawdown": -0.45,
            "win_rate": 0.4,
            "turnover": 9.0,
        },
        "report": {"grade": "偏弱", "conclusion": "..."},
        "cost_config": {"fee_rate": 0.0002, "slippage_bps": 1.0},
    }
    s = local_backtest_summary(ctx)
    assert any("回撤" in c for c in s["caveats"])
    assert any("换手" in c for c in s["caveats"])
    assert s["next_steps"]
    assert "偏弱" in s["headline"]


def test_backtest_summary_strong_recommends_validation():
    ctx = {
        "factor": {"name": "f2", "kind": "template"},
        "symbol": "CU",
        "metrics": {"annual_return": 0.4, "sharpe": 1.6, "max_drawdown": -0.1, "win_rate": 0.6, "turnover": 2.0},
        "report": {"grade": "优秀"},
        "cost_config": {},
    }
    s = local_backtest_summary(ctx)
    assert any("验证" in x for x in s["next_steps"])
    p = build_backtest_summary_prompt(ctx)
    assert p["system"] == MENTOR_SYSTEM
    assert "下一步" in p["user"]


def test_research_plan_has_hypotheses_and_no_trade_advice():
    plan = local_research_plan("黄金")
    assert plan["theme"] == "黄金"
    assert len(plan["hypotheses"]) >= 2
    assert all("factor_template" in h for h in plan["hypotheses"])
    assert plan["experiments"]
    assert plan["disclaimer"] == DISCLAIMER
    assert "黄金" in plan["markdown"] and "不构成" in plan["markdown"]


def test_research_plan_prompt_constrains_no_trade_signal():
    p = build_research_plan_prompt("螺纹钢")
    assert p["system"] == MENTOR_SYSTEM
    assert "螺纹钢" in p["user"]
    assert "不要" in p["user"]  # 约束: 不给买卖点/不承诺收益

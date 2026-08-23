"""Phase 3/4: AI strategy builder + MVP Chinese pipeline tests."""

from __future__ import annotations

from engine.ai.chinese_report import explain_backtest_zh
from engine.ai.mvp_pipeline import run_mvp_chinese_idea
from engine.ai.strategy_builder import build_strategy_from_chinese, confirm_draft
from engine.nautilus.availability import nautilus_available, nautilus_version
from engine.nautilus.backtest_adapter import PINNED_VERSION


def test_ambiguous_breakout_does_not_compile_live():
    r = build_strategy_from_chinese("黄金突破就买")
    assert r.ambiguous is True
    assert r.deployable is False
    assert r.draft_spec is None or r.draft_spec["strategy"]["deployable"] is False
    assert any("突破" in q.question_zh for q in r.questions)


def test_chinese_ema_draft_with_assumptions():
    text = (
        "欧元15分钟。EMA20上穿EMA60，同时ADX大于25做多。"
        "每笔最多亏0.5%。2倍ATR止损，4倍ATR止盈。"
        "每天最多亏2%。连续亏3笔以后停止交易。"
    )
    r = build_strategy_from_chinese(text)
    assert r.draft_spec is not None
    assert r.deployable is False
    assert r.draft_spec["deployment"]["permitted_environments"] == ["BACKTEST"]
    assert r.draft_spec["entry"]["long"]["conditions"][0]["params"]["fast"] == 20
    assert r.draft_spec["stop_loss"]["type"] == "atr_mult"
    assert r.draft_spec["stop_loss"]["value"] == 2.0
    assert "LIVE" not in r.draft_spec["deployment"]["permitted_environments"]


def test_confirm_still_denies_live():
    r = build_strategy_from_chinese("欧元美元15分钟 EMA10上穿EMA20")
    assert r.draft_spec is not None
    spec = confirm_draft(r.draft_spec, user_approved_rules=True)
    assert spec.strategy.user_approved is True
    assert spec.strategy.deployable is False
    assert "LIVE" not in spec.deployment.permitted_environments


def test_chinese_report_has_disclaimer_no_hype():
    rep = explain_backtest_zh(
        metrics={"sharpe": 1.42, "max_drawdown": -0.128, "fill_count": 34},
        strategy_name="测试策略",
        fill_count=34,
        ambiguous=False,
    )
    assert "不代表未来" in rep["disclaimer_zh"]
    assert "稳赚" not in rep["verdict_zh"]
    assert "最大回撤" in rep["terms_zh"]["max_drawdown"]


def test_mvp_eurusd_pipeline():
    text = "欧元美元15分钟。EMA10上穿EMA20做多做空。"
    out = run_mvp_chinese_idea(text, confirm=True)
    assert out["live_denied"] is True
    assert out["builder"]["deployable"] is False
    if nautilus_available() and nautilus_version() == PINNED_VERSION:
        assert out["status"] == "ok"
        assert out["backtest"]["engine"] == "NAUTILUS"
        assert "verdict_zh" in out["report_zh"]
    else:
        assert out["status"] in {"ok", "spec_ready_awaiting_matching_data", "compile_failed"}

"""QLN-4 Evidence Validation Pipeline tests."""

from __future__ import annotations

import pandas as pd
import pytest

from engine.evidence import (
    EVIDENCE_THRESHOLD_VERSION,
    apply_promotion_kill_rules,
    compute_reality_score,
    compute_research_debt,
    run_evidence_pipeline,
)
from engine.evidence.rules import EvidenceGates
from engine.evidence.thresholds import EVIDENCE_THRESHOLDS
from engine.nautilus.backtest_adapter import build_golden_ohlcv


def _ema_signal(fast: int, slow: int):
    def _fn(df: pd.DataFrame) -> pd.Series:
        c = df["close"].astype(float)
        return (c.ewm(span=fast, adjust=False).mean() > c.ewm(span=slow, adjust=False).mean()).astype(
            float
        )

    return _fn


def test_thresholds_frozen_version():
    assert EVIDENCE_THRESHOLD_VERSION == "qln4_evidence_thr_v1"
    assert EVIDENCE_THRESHOLDS["version"] == EVIDENCE_THRESHOLD_VERSION
    # Must not silently use promote-without-evidence
    assert EVIDENCE_THRESHOLDS["reality_promote_min"] >= 50


def test_evidence_pipeline_produces_decision():
    ohlcv = build_golden_ohlcv(n=400, seed=42)
    base = _ema_signal(10, 20)
    neighborhood = [
        ("f8_s20", _ema_signal(8, 20)),
        ("f10_s20", base),
        ("f12_s20", _ema_signal(12, 20)),
        ("f10_s24", _ema_signal(10, 24)),
    ]
    report = run_evidence_pipeline(
        strategy_id="golden_01_ema_trend",
        strategy_version="v1",
        ohlcv=ohlcv,
        compute_signal=base,
        neighborhood=neighborhood,
        param_count=2,
    )
    assert report.decision in ("PROMOTE", "HOLD", "KILL")
    assert report.live_execution == "DENY"
    assert report.threshold_version == EVIDENCE_THRESHOLD_VERSION
    assert "oos" in report.gates
    assert "fee_stress" in report.gates
    assert "slippage_stress" in report.gates
    assert "regime_split" in report.gates
    assert "extreme_period" in report.gates
    assert "score" in report.reality_score
    assert "score" in report.research_debt
    assert report.reasons
    # Decision must be explainable
    assert isinstance(report.reasons[0], str)


def test_kill_on_hard_fail_gate():
    gates = EvidenceGates(oos="FAIL")
    out = apply_promotion_kill_rules(
        gates, reality_score=90.0, research_debt=0.0, overfit_risk="LOW"
    )
    assert out.decision == "KILL"
    assert any("hard gate" in r for r in out.reasons)


def test_hold_when_insufficient():
    gates = EvidenceGates(
        backtest="PASS",
        oos="PASS",
        walk_forward="INSUFFICIENT",
        fee_stress="PASS",
        slippage_stress="PASS",
        parameter_sensitivity="PASS",
        regime_split="PASS",
        extreme_period="PASS",
    )
    out = apply_promotion_kill_rules(
        gates, reality_score=70.0, research_debt=10.0, overfit_risk="LOW"
    )
    assert out.decision == "HOLD"


def test_promote_requires_core_and_reality():
    gates = EvidenceGates(
        backtest="PASS",
        oos="PASS",
        walk_forward="PASS",
        fee_stress="PASS",
        slippage_stress="PASS",
        parameter_sensitivity="PASS",
        regime_split="PASS",
        extreme_period="PASS",
    )
    out = apply_promotion_kill_rules(
        gates, reality_score=70.0, research_debt=5.0, overfit_risk="LOW"
    )
    assert out.decision == "PROMOTE"


def test_reality_and_debt_helpers():
    rs = compute_reality_score(
        oos_flag="PASS",
        wf_flag="PASS",
        fee_flag="PASS",
        slip_flag="PASS",
        sens_flag="PASS",
        regime_flag="PASS",
        extreme_flag="PASS",
        oos_sharpe=1.0,
        wf_positive_ratio=0.8,
    )
    assert rs.score > 50
    debt = compute_research_debt(
        gates={"oos": "INSUFFICIENT"},
        overfit_risk="MEDIUM",
        trade_count=5,
        periods=50,
        min_trades=30,
        min_periods=200,
    )
    assert debt.score > 0
    assert debt.items


def test_empty_neighborhood_cannot_silently_pass_sensitivity():
    ohlcv = build_golden_ohlcv(n=200, seed=1)
    report = run_evidence_pipeline(
        strategy_id="x",
        strategy_version="v1",
        ohlcv=ohlcv,
        compute_signal=_ema_signal(10, 20),
        neighborhood=None,
        param_count=2,
    )
    assert report.gates["parameter_sensitivity"] in ("INSUFFICIENT", "FAIL")
    assert report.decision != "PROMOTE"

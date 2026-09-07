"""QLN-11 factor_sign → canonical Paper adapter tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.paper.canonical import PAPER_PATH_REGISTRY, PaperPathDisposition
from engine.paper.factor_sign_runtime import run_factor_sign_paper
from engine.paper.kill_switch import KillSwitchState
from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.factor_sign_adapter import compile_factor_sign_to_paper
from engine.strategies.v2.package import import_package
from engine.strategies.v2.spec_v2 import validate_spec_v2

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "strategy_specs" / "historical_reconstructed" / "hist_fl_momentum_w20.v2.package.json"
RB = ROOT / "data" / "market_data" / "genuine_recovery" / "RB_1d.parquet"
GOLDEN = ROOT / "strategy_specs" / "examples" / "golden_01_ema_trend.v1.yaml"


def _rb_tail(n: int = 300) -> pd.DataFrame:
    df = pd.read_parquet(RB)
    if df.index.tz is None:
        df = df.copy()
        df.index = pd.to_datetime(df.index).tz_localize("UTC")
    return df.sort_index().iloc[-n:]


def test_factor_sign_paper_registered_canonical():
    assert PAPER_PATH_REGISTRY["factor_sign_paper"]["disposition"] == PaperPathDisposition.CANONICAL.value
    assert PAPER_PATH_REGISTRY["paper_orders"]["disposition"] == PaperPathDisposition.SOFT_RETIRE.value


def test_compile_factor_sign_rb_and_refuse_ema():
    pkg = import_package(PKG)
    spec = validate_spec_v2(pkg.strategy_spec)
    c = compile_factor_sign_to_paper(spec, instrument="RB")
    assert c.instrument == "RB"
    assert c.execution_rule == "sign(signal)"
    assert c.lag_rule == "signal_t_affects_position_t_plus_1"
    assert c.template_type == "momentum"
    assert c.factor_params["window"] == 20
    with pytest.raises(SpecV2Error):
        compile_factor_sign_to_paper(spec, instrument="ZZ")


def test_semantic_parity_on_rb():
    pkg = import_package(PKG)
    spec = validate_spec_v2(pkg.strategy_spec)
    c = compile_factor_sign_to_paper(spec, instrument="RB")
    r = run_factor_sign_paper(c, _rb_tail(400))
    assert r.parity["FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY"] == "PASS"
    assert r.snapshot["PAPER_RUNTIME"] == "CANONICAL"
    assert r.snapshot["LEGACY_PAPER_ORDERS_USED"] == "NO"
    assert len(r.snapshot["orders"]) >= 1
    assert len(r.snapshot["fills"]) >= 1
    assert len(r.snapshot["signals"]) >= 1
    assert len(r.snapshot["positions"]) >= 1


def test_kill_and_recovery():
    pkg = import_package(PKG)
    spec = validate_spec_v2(pkg.strategy_spec)
    c = compile_factor_sign_to_paper(spec, instrument="RB")
    ohlcv = _rb_tail(150)
    killed = run_factor_sign_paper(
        c, ohlcv, kill_state=KillSwitchState(global_active=True, reason="test")
    )
    assert killed.kill_events
    recovered = run_factor_sign_paper(c, ohlcv, inject_restart_at=40)
    assert recovered.recovery_events


def test_synthetic_parity_momentum():
    idx = pd.date_range("2020-01-01", periods=80, freq="B", tz="UTC")
    rng = np.random.default_rng(7)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.01, size=len(idx)))
    ohlcv = pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": 1.0},
        index=idx,
    )
    pkg = import_package(PKG)
    spec = validate_spec_v2(pkg.strategy_spec)
    c = compile_factor_sign_to_paper(spec, instrument="RB")
    r = run_factor_sign_paper(c, ohlcv)
    assert r.parity["FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY"] == "PASS"

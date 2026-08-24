"""Strategy Spec semantic parity: Backtest and Paper must share compiled params."""

from __future__ import annotations

from pathlib import Path

import yaml

from engine.strategies.compiler import compile_spec, compile_deterministic
from engine.strategies.runtime_params import require_nautilus_runtime_params


def test_golden_spec_compiler_runtime_parity():
    path = Path(__file__).resolve().parents[2] / "strategy_specs/examples/golden_btc_ema_trend.v1.yaml"
    spec_payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    compiled_a = compile_deterministic(spec_payload)
    compiled_b = compile_deterministic(spec_payload)
    assert compiled_a == compiled_b

    runtime = require_nautilus_runtime_params(spec_payload)
    compiled = compile_spec(spec_payload)
    assert runtime["ema_fast"] == int(compiled.nautilus_params["fast_ema"])
    assert runtime["ema_slow"] == int(compiled.nautilus_params["slow_ema"])
    assert runtime["trade_size"] == str(compiled.nautilus_params["trade_size"])
    assert runtime["instrument"].replace("/", "") == str(compiled.nautilus_params["instrument"]).replace("/", "").upper()


def test_paper_node_rejects_missing_spec_params():
    from engine.nautilus.paper_node import PaperNodeConfig, run_paper_node

    snap = run_paper_node(
        PaperNodeConfig(
            run_id="missing-params",
            instrument="BTCUSDT",
            ema_fast=None,
            ema_slow=None,
            trade_size=None,
        )
    )
    assert snap.error
    assert "STRATEGY_SPEC_PARAMS_REQUIRED" in (snap.error or "")


def test_backtest_and_paper_share_ema_params():
    from engine.nautilus.availability import nautilus_available

    if not nautilus_available():
        return

    path = Path(__file__).resolve().parents[2] / "strategy_specs/examples/golden_btc_ema_trend.v1.yaml"
    spec_payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    runtime = require_nautilus_runtime_params(spec_payload)
    compiled = compile_spec(spec_payload)

    from engine.nautilus.backtest_adapter import NautilusBacktestAdapter

    adapter = NautilusBacktestAdapter()
    result = adapter.run_compiled_ema(
        compiled.nautilus_params,
        strategy_id=compiled.source_spec_id,
        strategy_version=compiled.source_spec_version,
    )
    assert result.status in {"ok", "success"}
    assert int(compiled.nautilus_params["fast_ema"]) == runtime["ema_fast"]
    assert int(compiled.nautilus_params["slow_ema"]) == runtime["ema_slow"]

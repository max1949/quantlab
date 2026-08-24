"""Phase 5 research loop: data gate, validation wiring, multi-instrument."""

from __future__ import annotations

import pandas as pd
import pytest

from engine.data.data_gate import DataProvenance, run_data_gate, user_facing_data_gate_message
from engine.data.dataset_resolver import resolve_dataset
from engine.nautilus.availability import nautilus_available, nautilus_version
from engine.nautilus.backtest_adapter import PINNED_VERSION, NautilusBacktestAdapter
from engine.strategies.lifecycle import run_validation_gate


def test_data_gate_pass_on_golden():
    _ref, df = resolve_dataset("EUR/USD")
    assert df is not None
    gate = run_data_gate(
        df,
        provenance=DataProvenance(
            provider="quantlab_golden",
            broker="SIM",
            symbol="EUR/USD",
            instrument="EUR/USD",
            broker_specific=True,
        ),
    )
    assert gate.status in {"PASS", "WARN"}
    msg = user_facing_data_gate_message(gate)
    assert "title_zh" in msg


def test_data_gate_fail_non_monotonic():
    idx = pd.to_datetime(["2024-01-02", "2024-01-01"], utc=True)
    df = pd.DataFrame(
        {"open": [1, 1], "high": [1, 1], "low": [1, 1], "close": [1, 1], "volume": [1, 1]},
        index=idx,
    )
    gate = run_data_gate(df)
    assert gate.status == "FAIL"
    assert any("递增" in i or "顺序" in i for i in gate.issues_zh)


def test_dataset_resolver_missing_instrument():
    ref, df = resolve_dataset("UNKNOWN_XYZ")
    assert ref.available is False
    assert df is None
    assert "没有可用" in ref.message_zh


def test_validation_gate_binds_spec_version():
    from engine.strategies import validate_spec
    import json
    from pathlib import Path

    data = json.loads(
        (Path(__file__).resolve().parents[2] / "strategy_specs/examples/golden_01_ema_trend.v1.json").read_text(
            encoding="utf-8"
        )
    )
    spec = validate_spec(data)
    _ref, ohlcv = resolve_dataset("EUR/USD")
    assert ohlcv is not None
    result = run_validation_gate(spec, ohlcv)
    assert result.strategy_spec_version == "v1"
    assert result.strategy_spec_id == "golden_01_ema_trend"
    assert result.paper_runtime is False
    assert result.lifecycle in {"DRAFT", "BACKTESTED", "VALIDATED", "ROBUST", "PAPER_READY"}


@pytest.mark.skipif(
    not nautilus_available() or nautilus_version() != PINNED_VERSION,
    reason="nautilus pinned env required",
)
def test_second_instrument_btc_e2e():
    _ref, ohlcv = resolve_dataset("BTCUSDT")
    assert ohlcv is not None
    gate = run_data_gate(
        ohlcv,
        provenance=DataProvenance(
            provider="quantlab_golden",
            broker="BINANCE_SIM",
            instrument="BTCUSDT",
            broker_specific=True,
        ),
    )
    assert gate.status != "FAIL"
    adapter = NautilusBacktestAdapter(require_pinned=True)
    result = adapter.run_ema_for_instrument(
        instrument="BTCUSDT",
        ohlcv=ohlcv,
        strategy_id="golden_02_btc_ema",
        strategy_version="v1",
    )
    assert result.status == "success"
    assert result.fill_count >= 1
    assert "BTCUSDT" in str(result.metrics.get("instrument", ""))

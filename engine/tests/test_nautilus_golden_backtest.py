"""Phase 1: Nautilus golden EMA backtest (requires nautilus_trader 1.231.0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.nautilus.availability import nautilus_available, nautilus_version
from engine.nautilus.backtest_adapter import (
    GOLDEN_STRATEGY_ID,
    PINNED_VERSION,
    NautilusBacktestAdapter,
    build_golden_ohlcv,
)

pytestmark = pytest.mark.skipif(
    not nautilus_available() or nautilus_version() != PINNED_VERSION,
    reason=f"requires nautilus_trader=={PINNED_VERSION} (use .venv-nautilus)",
)


def test_nautilus_import_pinned():
    assert nautilus_available()
    assert nautilus_version() == PINNED_VERSION


def test_golden_data_deterministic():
    a = build_golden_ohlcv()
    b = build_golden_ohlcv()
    assert len(a) == 400
    assert a["close"].equals(b["close"])
    assert float(a["close"].iloc[0]) != float(a["close"].iloc[-1])


def test_golden_ema_backtest_persists(tmp_path: Path):
    adapter = NautilusBacktestAdapter(require_pinned=True)
    result = adapter.run_ema_golden(persist_dir=tmp_path)
    assert result.status == "success"
    assert result.engine == "NAUTILUS"
    assert result.engine_version == PINNED_VERSION
    assert result.strategy_id == GOLDEN_STRATEGY_ID
    assert result.fill_count >= 1
    assert result.position_count >= 1
    saved = tmp_path / f"{GOLDEN_STRATEGY_ID}_{result.strategy_version}.json"
    assert saved.is_file()
    text = saved.read_text(encoding="utf-8")
    assert "NAUTILUS" in text

"""Nautilus adapter façade satisfying Domain BacktestEngineContract (no Nautilus types leak)."""

from __future__ import annotations

from typing import Any

from engine.domain.engine_contracts import (
    BacktestEngineContract,
    BacktestRequest,
    BacktestResultContract,
    EngineCapability,
)
from engine.domain.hashing import fingerprint_engine, hash_strategy_definition
from engine.strategies.compiler import compile_spec
from engine.strategies.runtime_params import require_nautilus_runtime_params


class NautilusBacktestPort:
    """Domain port → NautilusBacktestAdapter (lazy import)."""

    def capabilities(self) -> EngineCapability:
        return EngineCapability(
            name="nautilus_backtest",
            supports_backtest=True,
            supports_paper=False,
            supports_shadow=False,
            supports_live=False,
            notes="Canonical higher-fidelity backtest kernel adapter",
        )

    def run_backtest(self, request: BacktestRequest) -> BacktestResultContract:
        from engine.nautilus.availability import nautilus_available

        spec_hash = ""
        try:
            spec_hash = hash_strategy_definition(request.strategy_spec)
            if not nautilus_available():
                return BacktestResultContract(
                    ok=False,
                    strategy_spec_hash=spec_hash,
                    error="nautilus_trader not available",
                )
            from engine.nautilus.backtest_adapter import NautilusBacktestAdapter

            runtime = require_nautilus_runtime_params(request.strategy_spec)
            compiled = compile_spec(request.strategy_spec)
            adapter = NautilusBacktestAdapter(
                require_pinned=bool(request.params.get("require_pinned", True))
            )
            result = adapter.run_compiled_ema(
                compiled.nautilus_params,
                strategy_id=compiled.source_spec_id,
                strategy_version=compiled.source_spec_version,
            )
            metrics: dict[str, Any] = result.to_dict() if hasattr(result, "to_dict") else {}
            ok = getattr(result, "status", "") in {"ok", "success"}
            return BacktestResultContract(
                ok=ok,
                strategy_spec_hash=spec_hash or str(runtime.get("compiled_hash") or ""),
                metrics=metrics,
                engine_fingerprint=fingerprint_engine(
                    engine_name="nautilus",
                    engine_version=str(getattr(adapter, "engine_version", "unknown")),
                    adapter_version="nautilus_backtest_port.v1",
                ),
            )
        except Exception as exc:  # noqa: BLE001 — domain port must fail closed
            return BacktestResultContract(
                ok=False,
                strategy_spec_hash=spec_hash,
                error=str(exc),
            )


def as_backtest_engine() -> BacktestEngineContract:
    return NautilusBacktestPort()

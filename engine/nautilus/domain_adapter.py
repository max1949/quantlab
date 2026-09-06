"""Nautilus adapter façades for Domain engine contracts (no Nautilus types leak)."""

from __future__ import annotations

from typing import Any

from engine.domain.engine_contracts import (
    BacktestEngineContract,
    BacktestRequest,
    BacktestResultContract,
    EngineCapability,
    PaperRuntimeContract,
    PaperRuntimeRequest,
    RuntimeResultContract,
)
from engine.domain.enums import ExecutionMode
from engine.domain.environment import Environment, assert_environment_allowed
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


class NautilusPaperRuntimePort:
    """Domain PaperRuntimeContract — validates Spec/env; process orchestration stays in app layer.

    QLN-1 scope: lock interface + LIVE deny + Spec SSOT. Full runner wire-through is QLN-5.
    """

    def __init__(self) -> None:
        self._accepted: dict[str, str] = {}

    def capabilities(self) -> EngineCapability:
        return EngineCapability(
            name="nautilus_paper",
            supports_backtest=False,
            supports_paper=True,
            supports_shadow=False,
            supports_live=False,
            notes="Official Paper path port; LIVE always denied",
        )

    def start(self, request: PaperRuntimeRequest) -> RuntimeResultContract:
        try:
            if request.execution_mode == ExecutionMode.LIVE:
                return RuntimeResultContract(
                    ok=False,
                    run_id=request.run_id,
                    status="DENIED",
                    error="LIVE execution mode DENY",
                )
            if request.environment == Environment.LIVE:
                return RuntimeResultContract(
                    ok=False,
                    run_id=request.run_id,
                    status="DENIED",
                    error="LIVE environment DENY",
                )
            assert_environment_allowed(request.environment, live_allowed=False)
            # Shared Spec semantics with backtest
            require_nautilus_runtime_params(
                request.strategy_spec or request.effective_config.get("spec") or request.effective_config
            )
            self._accepted[request.run_id] = "START_ACCEPTED"
            return RuntimeResultContract(
                ok=True,
                run_id=request.run_id,
                status="START_ACCEPTED",
            )
        except Exception as exc:  # noqa: BLE001
            return RuntimeResultContract(
                ok=False,
                run_id=request.run_id,
                status="FAILED",
                error=str(exc),
            )

    def stop(self, run_id: str) -> RuntimeResultContract:
        if run_id in self._accepted:
            self._accepted[run_id] = "STOPPED"
            return RuntimeResultContract(ok=True, run_id=run_id, status="STOPPED")
        return RuntimeResultContract(
            ok=False,
            run_id=run_id,
            status="UNKNOWN_RUN",
            error="run_id not accepted by this port instance",
        )


def as_backtest_engine() -> BacktestEngineContract:
    return NautilusBacktestPort()


def as_paper_runtime() -> PaperRuntimeContract:
    return NautilusPaperRuntimePort()

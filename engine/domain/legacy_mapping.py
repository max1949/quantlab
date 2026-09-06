"""Legacy → Canonical domain mapping (classify only actions; no destructive retirement)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from engine.domain.enums import ExecutionMode, StrategyLifecycle
from engine.domain.environment import Environment


class LegacyDisposition(str, Enum):
    KEEP = "KEEP"
    HARDEN = "HARDEN"
    MERGE = "MERGE"
    MIGRATE = "MIGRATE"
    SOFT_RETIRE = "SOFT_RETIRE"
    ARCHIVE = "ARCHIVE"


@dataclass(frozen=True, slots=True)
class LegacyMapRow:
    legacy_value: str
    canonical_value: str
    disposition: LegacyDisposition
    notes: str


STRATEGY_LIFECYCLE_LEGACY: tuple[LegacyMapRow, ...] = (
    LegacyMapRow("DRAFT", StrategyLifecycle.DRAFT.value, LegacyDisposition.MIGRATE, "engine.strategies.lifecycle"),
    LegacyMapRow("BACKTESTED", StrategyLifecycle.RESEARCH_ACTIVE.value, LegacyDisposition.MIGRATE, "historical Spec gate"),
    LegacyMapRow("VALIDATED", StrategyLifecycle.CANDIDATE.value, LegacyDisposition.MIGRATE, "OOS/WF passed label"),
    LegacyMapRow("ROBUST", StrategyLifecycle.CANDIDATE.value, LegacyDisposition.MIGRATE, "robustness passed"),
    LegacyMapRow("PAPER_READY", StrategyLifecycle.PAPER_APPROVED.value, LegacyDisposition.MIGRATE, "PaperReadyRegistry"),
)

ENVIRONMENT_LEGACY: tuple[LegacyMapRow, ...] = (
    LegacyMapRow("SANDBOX", Environment.PAPER.value, LegacyDisposition.MERGE, "Phase-6 SANDBOX ≡ PAPER env"),
    LegacyMapRow("PAPER", Environment.PAPER.value, LegacyDisposition.KEEP, "already canonical"),
    LegacyMapRow("BACKTEST", Environment.BACKTEST.value, LegacyDisposition.KEEP, ""),
    LegacyMapRow("SHADOW", Environment.SHADOW.value, LegacyDisposition.KEEP, "capability not built"),
    LegacyMapRow("LIVE", Environment.LIVE.value, LegacyDisposition.HARDEN, "LIVE_DEFAULT=DENY"),
    LegacyMapRow("SIM", Environment.BACKTEST.value, LegacyDisposition.MERGE, "legacy venue/env alias"),
)

EXECUTION_CHANNEL_LEGACY: tuple[LegacyMapRow, ...] = (
    LegacyMapRow("paper", ExecutionMode.PAPER.value, LegacyDisposition.SOFT_RETIRE, "legacy paper_orders channel"),
    LegacyMapRow("vnpy", ExecutionMode.NO_EXECUTION.value, LegacyDisposition.ARCHIVE, "NEW_CREATE=DENY"),
    LegacyMapRow("qmt", ExecutionMode.NO_EXECUTION.value, LegacyDisposition.SOFT_RETIRE, "NEW_CREATE=DENY"),
    LegacyMapRow("nautilus_paper", ExecutionMode.PAPER.value, LegacyDisposition.KEEP, "official PaperRun"),
    LegacyMapRow("vectorized_sim", ExecutionMode.SIMULATION.value, LegacyDisposition.KEEP, "Factor Lab backtest"),
)

PAPER_RUN_STATUS_LEGACY: tuple[LegacyMapRow, ...] = (
    LegacyMapRow("CREATED", "RUN.CREATED", LegacyDisposition.KEEP, "PaperRunStatus — run state ≠ strategy lifecycle"),
    LegacyMapRow("STARTING", "RUN.STARTING", LegacyDisposition.KEEP, "different domain: Run"),
    LegacyMapRow("RUNNING", "RUN.RUNNING", LegacyDisposition.KEEP, "not StrategyLifecycle.RESEARCH_ACTIVE"),
    LegacyMapRow("PAUSED", "RUN.PAUSED", LegacyDisposition.KEEP, ""),
    LegacyMapRow("STOPPING", "RUN.STOPPING", LegacyDisposition.KEEP, ""),
    LegacyMapRow("STOPPED", "RUN.STOPPED", LegacyDisposition.KEEP, ""),
    LegacyMapRow("FAILED", "RUN.FAILED", LegacyDisposition.KEEP, ""),
    LegacyMapRow("KILLED", "RUN.KILLED", LegacyDisposition.KEEP, ""),
)

ASSET_DISPOSITIONS: tuple[LegacyMapRow, ...] = (
    LegacyMapRow("engine/backtest.py", "ExecutionMode.SIMULATION + Research OS", LegacyDisposition.KEEP, "Factor Lab"),
    LegacyMapRow("engine/nautilus/backtest_adapter.py", "BacktestEngineContract impl", LegacyDisposition.KEEP, "official BT"),
    LegacyMapRow("engine.trading.AdapterBacktestRequest", "adapter transport ≠ domain BacktestRequest", LegacyDisposition.MERGE, "QLN-1 renamed from BacktestRequest"),
    LegacyMapRow("PaperRun", "Environment.PAPER + ExecutionMode.PAPER", LegacyDisposition.KEEP, "official paper"),
    LegacyMapRow("paper_orders", "legacy ExecutionMode.PAPER coaching", LegacyDisposition.SOFT_RETIRE, "FE still callable"),
    LegacyMapRow("execution_adapter", "SOFT_RETIRE residual", LegacyDisposition.SOFT_RETIRE, "_route_gateway latent"),
    LegacyMapRow("sandbox_runtime", "non-canonical scaffold", LegacyDisposition.SOFT_RETIRE, "not official runner"),
    LegacyMapRow("QMT", "NO_EXECUTION", LegacyDisposition.SOFT_RETIRE, ""),
    LegacyMapRow("vn.py", "NO_EXECUTION", LegacyDisposition.ARCHIVE, ""),
    LegacyMapRow("Strategy Spec v1", "strategy definition contract", LegacyDisposition.MIGRATE, "QLN-2 Spec v2"),
)


def map_legacy_strategy_lifecycle(raw: str) -> StrategyLifecycle:
    key = (raw or "").strip().upper()
    for row in STRATEGY_LIFECYCLE_LEGACY:
        if row.legacy_value == key:
            return StrategyLifecycle(row.canonical_value)
    try:
        return StrategyLifecycle(key)
    except ValueError as exc:
        raise ValueError(f"unknown legacy strategy lifecycle: {raw}") from exc


def map_legacy_environment(raw: str) -> Environment:
    from engine.domain.environment import normalize_environment

    return normalize_environment(raw)


def map_legacy_execution_channel(raw: str) -> ExecutionMode:
    key = (raw or "").strip().lower()
    for row in EXECUTION_CHANNEL_LEGACY:
        if row.legacy_value == key:
            return ExecutionMode(row.canonical_value)
    raise ValueError(f"unknown legacy execution channel: {raw}")


def map_legacy_paper_run_status(raw: str) -> str:
    key = (raw or "").strip().upper()
    for row in PAPER_RUN_STATUS_LEGACY:
        if row.legacy_value == key:
            return row.canonical_value
    raise ValueError(f"unknown paper run status: {raw}")

"""Execution environment enum + application gates (LIVE always denied in Phase 6)."""

from __future__ import annotations

from enum import Enum
from typing import Literal

GateVerdict = Literal["ALLOW", "DENY"]


class ExecutionEnvironment(str, Enum):
    BACKTEST = "BACKTEST"
    SANDBOX = "SANDBOX"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    LIVE = "LIVE"


PHASE6_ALLOWED = frozenset(
    {
        ExecutionEnvironment.BACKTEST,
        ExecutionEnvironment.SANDBOX,
        ExecutionEnvironment.PAPER,
        ExecutionEnvironment.SHADOW,
    }
)


class EnvironmentGateError(Exception):
    def __init__(self, message: str, *, environment: str, layer: str) -> None:
        super().__init__(message)
        self.environment = environment
        self.layer = layer


def normalize_environment(value: str | ExecutionEnvironment) -> ExecutionEnvironment:
    if isinstance(value, ExecutionEnvironment):
        return value
    raw = (value or "").strip().upper()
    try:
        return ExecutionEnvironment(raw)
    except ValueError as exc:
        raise EnvironmentGateError(
            f"无效执行环境: {value}",
            environment=str(value),
            layer="application",
        ) from exc


def assert_environment_allowed(
    environment: str | ExecutionEnvironment,
    *,
    layer: str = "application",
    live_allowed: bool = False,
    allowed: frozenset[ExecutionEnvironment] | None = None,
) -> ExecutionEnvironment:
    """Triple-gate helper: UI / backend / adapter all call this."""
    env = normalize_environment(environment)
    if env == ExecutionEnvironment.LIVE and not live_allowed:
        raise EnvironmentGateError(
            "LIVE 执行环境已禁用（LIVE=DENY）。Phase 6 仅允许 BACKTEST/SANDBOX/PAPER/SHADOW。",
            environment=env.value,
            layer=layer,
        )
    allowed_set = allowed or PHASE6_ALLOWED
    if env not in allowed_set:
        raise EnvironmentGateError(
            f"执行环境 {env.value} 不在允许列表: {sorted(e.value for e in allowed_set)}",
            environment=env.value,
            layer=layer,
        )
    return env


def gate_verdict(
    environment: str | ExecutionEnvironment,
    *,
    live_allowed: bool = False,
) -> GateVerdict:
    try:
        assert_environment_allowed(environment, live_allowed=live_allowed)
        return "ALLOW"
    except EnvironmentGateError:
        return "DENY"

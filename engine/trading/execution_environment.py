"""Execution environment enum + application gates.

QLN-1: compatibility facade over engine.domain.environment.
Legacy SANDBOX continues to work and normalizes to Environment.PAPER.
LIVE remains DENY by default.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from engine.domain.environment import (
    DEFAULT_ALLOWED as _DOMAIN_DEFAULT_ALLOWED,
    Environment as DomainEnvironment,
    EnvironmentGateError,
    LIVE_DEFAULT_DENY,
    assert_environment_allowed as domain_assert_environment_allowed,
    gate_verdict as domain_gate_verdict,
    normalize_environment as domain_normalize_environment,
)

GateVerdict = Literal["ALLOW", "DENY"]


class ExecutionEnvironment(str, Enum):
    """Legacy-compatible env enum used by PaperRun / Phase-6 call sites.

    Canonical domain Environment is the SSOT. SANDBOX is retained as a
    legacy alias that maps to PAPER in the domain layer.
    """

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


def _to_legacy(env: DomainEnvironment) -> ExecutionEnvironment:
    if env == DomainEnvironment.PAPER:
        # Prefer PAPER when caller used PAPER; SANDBOX callers keep string via normalize path.
        return ExecutionEnvironment.PAPER
    if env == DomainEnvironment.BACKTEST:
        return ExecutionEnvironment.BACKTEST
    if env == DomainEnvironment.SHADOW:
        return ExecutionEnvironment.SHADOW
    if env == DomainEnvironment.LIVE:
        return ExecutionEnvironment.LIVE
    if env in (DomainEnvironment.TEST, DomainEnvironment.DEVELOPMENT):
        return ExecutionEnvironment.BACKTEST
    if env == DomainEnvironment.CANARY:
        # Not in legacy enum — surface as LIVE-gated denial upstream.
        return ExecutionEnvironment.LIVE
    return ExecutionEnvironment.PAPER


def normalize_environment(value: str | ExecutionEnvironment | DomainEnvironment) -> ExecutionEnvironment:
    if isinstance(value, ExecutionEnvironment):
        # SANDBOX remains a valid legacy enum member.
        return value
    domain_env = domain_normalize_environment(
        value.value if isinstance(value, DomainEnvironment) else value
    )
    raw = (value if isinstance(value, str) else getattr(value, "value", "")).strip().upper()
    if raw == "SANDBOX":
        return ExecutionEnvironment.SANDBOX
    return _to_legacy(domain_env)


def assert_environment_allowed(
    environment: str | ExecutionEnvironment | DomainEnvironment,
    *,
    layer: str = "application",
    live_allowed: bool = False,
    allowed: frozenset[ExecutionEnvironment] | None = None,
) -> ExecutionEnvironment:
    """Triple-gate helper: UI / backend / adapter all call this."""
    # Preserve legacy allow-list semantics (SANDBOX + PAPER both OK).
    if allowed is not None:
        legacy = normalize_environment(environment)
        if legacy == ExecutionEnvironment.LIVE and not live_allowed:
            raise EnvironmentGateError(
                "LIVE 执行环境已禁用（LIVE=DENY）。Phase 6 仅允许 BACKTEST/SANDBOX/PAPER/SHADOW。",
                environment=legacy.value,
                layer=layer,
            )
        if legacy not in allowed:
            raise EnvironmentGateError(
                f"执行环境 {legacy.value} 不在允许列表: {sorted(e.value for e in allowed)}",
                environment=legacy.value,
                layer=layer,
            )
        return legacy

    domain_assert_environment_allowed(
        environment if not isinstance(environment, ExecutionEnvironment) else environment.value,
        layer=layer,
        live_allowed=live_allowed,
    )
    return normalize_environment(environment)


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


# Re-exports for callers / tests
__all__ = [
    "ExecutionEnvironment",
    "EnvironmentGateError",
    "GateVerdict",
    "PHASE6_ALLOWED",
    "LIVE_DEFAULT_DENY",
    "DomainEnvironment",
    "assert_environment_allowed",
    "gate_verdict",
    "normalize_environment",
    "_DOMAIN_DEFAULT_ALLOWED",
    "domain_gate_verdict",
]

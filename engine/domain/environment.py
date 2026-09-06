"""Canonical Environment enum + LIVE fail-closed gates (QLN-1)."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from engine.domain.enums import DomainError

GateVerdict = Literal["ALLOW", "DENY"]

LIVE_DEFAULT_DENY = True


class Environment(str, Enum):
    """Runtime/deployment environment — NOT StrategyLifecycle and NOT EvidenceStage."""

    TEST = "TEST"
    DEVELOPMENT = "DEVELOPMENT"
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    CANARY = "CANARY"
    LIVE = "LIVE"


# Default allow-set until Owner authorizes Canary/Live.
DEFAULT_ALLOWED = frozenset(
    {
        Environment.TEST,
        Environment.DEVELOPMENT,
        Environment.BACKTEST,
        Environment.PAPER,
        Environment.SHADOW,
    }
)

# Legacy string aliases → canonical Environment (not second definitions).
_LEGACY_ENV_ALIASES = {
    "SANDBOX": Environment.PAPER,
    "PAPER_SANDBOX": Environment.PAPER,
    "SIM": Environment.BACKTEST,
    "SIMULATION": Environment.BACKTEST,
    "DEV": Environment.DEVELOPMENT,
    "PROD": Environment.LIVE,  # still gated DENY unless live_allowed
}


class EnvironmentGateError(DomainError):
    def __init__(self, message: str, *, environment: str, layer: str) -> None:
        super().__init__(message)
        self.environment = environment
        self.layer = layer


def normalize_environment(value: str | Environment) -> Environment:
    if isinstance(value, Environment):
        return value
    raw = (value or "").strip().upper()
    if raw in _LEGACY_ENV_ALIASES:
        return _LEGACY_ENV_ALIASES[raw]
    try:
        return Environment(raw)
    except ValueError as exc:
        raise EnvironmentGateError(
            f"无效执行环境: {value}",
            environment=str(value),
            layer="domain",
        ) from exc


def assert_environment_allowed(
    environment: str | Environment,
    *,
    layer: str = "domain",
    live_allowed: bool = False,
    canary_allowed: bool = False,
    allowed: frozenset[Environment] | None = None,
) -> Environment:
    env = normalize_environment(environment)
    if env == Environment.LIVE and not live_allowed:
        raise EnvironmentGateError(
            "LIVE 执行环境已禁用（LIVE_DEFAULT=DENY）。",
            environment=env.value,
            layer=layer,
        )
    if env == Environment.CANARY and not canary_allowed:
        raise EnvironmentGateError(
            "CANARY 环境未授权（QLN-1 默认 DENY）。",
            environment=env.value,
            layer=layer,
        )
    allowed_set = set(allowed or DEFAULT_ALLOWED)
    if live_allowed:
        allowed_set.add(Environment.LIVE)
    if canary_allowed:
        allowed_set.add(Environment.CANARY)
    if env not in allowed_set:
        raise EnvironmentGateError(
            f"执行环境 {env.value} 不在允许列表: {sorted(e.value for e in allowed_set)}",
            environment=env.value,
            layer=layer,
        )
    return env


def gate_verdict(
    environment: str | Environment,
    *,
    live_allowed: bool = False,
    canary_allowed: bool = False,
) -> GateVerdict:
    try:
        assert_environment_allowed(
            environment, live_allowed=live_allowed, canary_allowed=canary_allowed
        )
        return "ALLOW"
    except EnvironmentGateError:
        return "DENY"

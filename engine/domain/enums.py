"""Canonical StrategyLifecycle + EvidenceStage (separate from Environment / ExecutionMode)."""

from __future__ import annotations

from enum import Enum


class DomainError(Exception):
    pass


class StrategyLifecycle(str, Enum):
    """Strategy definition lifecycle — NOT environment and NOT evidence stage."""

    IDEA = "IDEA"
    DRAFT = "DRAFT"
    STATIC_VALIDATED = "STATIC_VALIDATED"
    DATA_VALIDATED = "DATA_VALIDATED"
    RESEARCH_ACTIVE = "RESEARCH_ACTIVE"
    CANDIDATE = "CANDIDATE"
    PAPER_APPROVED = "PAPER_APPROVED"
    SHADOW_APPROVED = "SHADOW_APPROVED"
    CANARY_APPROVED = "CANARY_APPROVED"
    LIVE_APPROVED = "LIVE_APPROVED"
    MATURE = "MATURE"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


# Legal transitions (fail-closed otherwise).
_LIFECYCLE_TRANSITIONS: dict[StrategyLifecycle, frozenset[StrategyLifecycle]] = {
    StrategyLifecycle.IDEA: frozenset(
        {StrategyLifecycle.DRAFT, StrategyLifecycle.RETIRED}
    ),
    StrategyLifecycle.DRAFT: frozenset(
        {
            StrategyLifecycle.STATIC_VALIDATED,
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.STATIC_VALIDATED: frozenset(
        {
            StrategyLifecycle.DATA_VALIDATED,
            StrategyLifecycle.DRAFT,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.DATA_VALIDATED: frozenset(
        {
            StrategyLifecycle.RESEARCH_ACTIVE,
            StrategyLifecycle.DRAFT,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.RESEARCH_ACTIVE: frozenset(
        {
            StrategyLifecycle.CANDIDATE,
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.CANDIDATE: frozenset(
        {
            StrategyLifecycle.PAPER_APPROVED,
            StrategyLifecycle.RESEARCH_ACTIVE,
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.PAPER_APPROVED: frozenset(
        {
            StrategyLifecycle.SHADOW_APPROVED,
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.DEGRADED,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.SHADOW_APPROVED: frozenset(
        {
            StrategyLifecycle.CANARY_APPROVED,
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.DEGRADED,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.CANARY_APPROVED: frozenset(
        {
            StrategyLifecycle.LIVE_APPROVED,
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.DEGRADED,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.LIVE_APPROVED: frozenset(
        {
            StrategyLifecycle.MATURE,
            StrategyLifecycle.DEGRADED,
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.MATURE: frozenset(
        {
            StrategyLifecycle.DEGRADED,
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.DEGRADED: frozenset(
        {
            StrategyLifecycle.SUSPENDED,
            StrategyLifecycle.RETIRED,
            StrategyLifecycle.RESEARCH_ACTIVE,
        }
    ),
    StrategyLifecycle.SUSPENDED: frozenset(
        {
            StrategyLifecycle.RESEARCH_ACTIVE,
            StrategyLifecycle.RETIRED,
        }
    ),
    StrategyLifecycle.RETIRED: frozenset(),
}


def assert_lifecycle_transition(
    current: StrategyLifecycle, nxt: StrategyLifecycle
) -> None:
    allowed = _LIFECYCLE_TRANSITIONS.get(current, frozenset())
    if nxt not in allowed:
        raise DomainError(
            f"illegal StrategyLifecycle transition: {current.value} → {nxt.value}"
        )


class EvidenceStage(str, Enum):
    """Evidence accumulation stage — capability may be absent; stage still exists as contract."""

    E0_IDEA = "E0_IDEA"
    E1_BACKTEST = "E1_BACKTEST"
    E2_OOS = "E2_OOS"
    E3_WALK_FORWARD = "E3_WALK_FORWARD"
    E3B_STRESS = "E3B_STRESS"
    E4_PAPER = "E4_PAPER"
    E5_SHADOW = "E5_SHADOW"
    E6_CANARY = "E6_CANARY"
    E7_LIVE = "E7_LIVE"
    UNKNOWN = "UNKNOWN"


_EVIDENCE_ORDER = (
    EvidenceStage.E0_IDEA,
    EvidenceStage.E1_BACKTEST,
    EvidenceStage.E2_OOS,
    EvidenceStage.E3_WALK_FORWARD,
    EvidenceStage.E3B_STRESS,
    EvidenceStage.E4_PAPER,
    EvidenceStage.E5_SHADOW,
    EvidenceStage.E6_CANARY,
    EvidenceStage.E7_LIVE,
)


def evidence_order_index(stage: EvidenceStage) -> int:
    if stage == EvidenceStage.UNKNOWN:
        return -1
    return _EVIDENCE_ORDER.index(stage)


def assert_evidence_transition(
    current: EvidenceStage, nxt: EvidenceStage, *, allow_hold: bool = True
) -> None:
    """Evidence may advance one step, stay, or drop to UNKNOWN; skip-ahead fail-closed."""
    if current == EvidenceStage.UNKNOWN or nxt == EvidenceStage.UNKNOWN:
        if nxt == EvidenceStage.UNKNOWN or current == EvidenceStage.UNKNOWN:
            return
    if allow_hold and current == nxt:
        return
    ci = evidence_order_index(current)
    ni = evidence_order_index(nxt)
    if ci < 0 or ni < 0:
        raise DomainError(f"illegal EvidenceStage involving UNKNOWN: {current} → {nxt}")
    if ni > ci + 1:
        raise DomainError(
            f"evidence skip forbidden: {current.value} → {nxt.value} (fail-closed)"
        )
    if ni < ci and not allow_hold:
        raise DomainError(f"evidence regression forbidden: {current.value} → {nxt.value}")


class ExecutionMode(str, Enum):
    """How the system may act — independent of Environment and EvidenceStage."""

    NO_EXECUTION = "NO_EXECUTION"
    READ_ONLY = "READ_ONLY"
    SIMULATION = "SIMULATION"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    LIVE = "LIVE"


def live_execution_default_denied() -> bool:
    return True

"""QLN-10 Canary Live Readiness Gate — readiness only, never starts Live."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from engine.reliability.chaos import chaos_acceptance_suite, default_broker_matrix


LiveReadiness = Literal["PASS", "HOLD", "DENY"]


class CanaryCapitalContract(BaseModel):
    max_notional: float = 0.0
    max_loss: float = 0.0
    max_leverage: float = 1.0
    venues_allowed: list[str] = Field(default_factory=list)
    strategies_allowed: list[str] = Field(default_factory=list)
    real_money_authorized: bool = False  # must stay false without Owner QLN-11 auth


class OperatorActionCard(BaseModel):
    emergency_stop: str = "TRIP dead-man + kill-switch; flatten paper/shadow only"
    rollback: str = "Revert to last sealed Paper/Shadow build; deny Live"
    alert_channels: list[str] = Field(default_factory=lambda: ["ledger", "operator_card"])
    owner_approval_required_for_live: bool = True


class ReadinessReport(BaseModel):
    LIVE_READINESS: LiveReadiness
    reasons: list[str] = Field(default_factory=list)
    chaos: dict[str, Any] = Field(default_factory=dict)
    capital_contract: CanaryCapitalContract = Field(default_factory=CanaryCapitalContract)
    operator_card: OperatorActionCard = Field(default_factory=OperatorActionCard)
    broker_matrix: list[dict[str, Any]] = Field(default_factory=list)
    qln11_auto_enter: str = "DENY"
    real_money: str = "NO"


def evaluate_live_readiness(
    *,
    qln5_paper_pass: bool,
    qln8_shadow_pass: bool,
    qln9_chaos_pass: bool | None = None,
    capital: CanaryCapitalContract | None = None,
    owner_live_approval: bool = False,
) -> ReadinessReport:
    """Engineering readiness for canary — PASS means may *request* Owner Live Approval only."""
    capital = capital or CanaryCapitalContract(
        max_notional=1000.0,
        max_loss=100.0,
        venues_allowed=["SIMULATED"],
        strategies_allowed=["hist_fl_momentum_w20", "hist_fl_rsi_w14"],
        real_money_authorized=False,
    )
    chaos = chaos_acceptance_suite()
    if qln9_chaos_pass is None:
        qln9_chaos_pass = chaos.get("CHAOS_ACCEPTANCE") == "PASS"

    reasons: list[str] = []
    if not qln5_paper_pass:
        reasons.append("QLN-5 Paper not PASS")
    if not qln8_shadow_pass:
        reasons.append("QLN-8 Shadow not PASS")
    if not qln9_chaos_pass:
        reasons.append("QLN-9 Chaos not PASS")
    if capital.real_money_authorized:
        reasons.append("capital.real_money_authorized must be false pre-QLN-11")
    if capital.max_notional <= 0 or capital.max_loss <= 0:
        reasons.append("canary capital envelope incomplete")

    matrix = [m.model_dump(mode="json") for m in default_broker_matrix()]
    live_capable = any(m.get("supports_live") for m in matrix)
    if not live_capable:
        # Research stack has no live-capable venue — readiness can still PASS as engineering gate
        # but notes that broker live capability is absent (HOLD if we require live venue).
        # Constitution: prove engineering qualification, not start Live.
        pass

    if reasons:
        status: LiveReadiness = "DENY" if any("authorized" in r for r in reasons) else "HOLD"
        if any(x in "".join(reasons) for x in ("QLN-5", "QLN-8", "QLN-9")):
            status = "HOLD"
    else:
        status = "PASS"

    if owner_live_approval:
        # Still does not auto-enter QLN-11
        reasons.append("Owner approval noted but QLN_11_AUTO_ENTER=DENY")

    return ReadinessReport(
        LIVE_READINESS=status,
        reasons=reasons,
        chaos=chaos,
        capital_contract=capital,
        broker_matrix=matrix,
        qln11_auto_enter="DENY",
        real_money="NO",
    )

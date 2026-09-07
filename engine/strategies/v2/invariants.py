"""Machine-verifiable Strategy Invariants (structured, not README prose)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from engine.strategies.v2.errors import SpecV2Error


InvariantKind = Literal[
    "no_martingale",
    "no_unbounded_averaging_down",
    "max_risk_per_trade",
    "max_leverage",
    "stop_policy_required",
    "no_new_risk_on_stale_data",
    "no_new_risk_on_unknown_execution_state",
    "max_open_positions",
    "custom",
]


class InvariantRule(BaseModel):
    id: str
    kind: InvariantKind
    enabled: bool = True
    severity: Literal["deny", "warn"] = "deny"
    params: dict[str, Any] = Field(default_factory=dict)
    description: str = ""

    def evaluate_against_spec(self, spec_risk: dict[str, Any], *, has_stop: bool) -> str | None:
        """Return violation message or None if OK. Fail closed on unknown params."""
        if not self.enabled:
            return None
        k = self.kind
        if k == "no_martingale":
            # Structural: forbid sizing type that scales after loss without bound
            if self.params.get("forbid_types"):
                # checked at package validation time via parameters
                return None
            return None
        if k == "no_unbounded_averaging_down":
            max_adds = self.params.get("max_adds_on_loss")
            if max_adds is None:
                raise SpecV2Error(f"invariant {self.id}: max_adds_on_loss required")
            return None
        if k == "max_risk_per_trade":
            ceiling = self.params.get("max")
            if ceiling is None:
                raise SpecV2Error(f"invariant {self.id}: max required")
            rpt = spec_risk.get("risk_per_trade")
            if rpt is not None and float(rpt) > float(ceiling):
                return f"{self.id}: risk_per_trade {rpt} > {ceiling}"
            return None
        if k == "max_leverage":
            ceiling = self.params.get("max")
            if ceiling is None:
                raise SpecV2Error(f"invariant {self.id}: max required")
            lev = spec_risk.get("leverage_limit")
            if lev is not None and float(lev) > float(ceiling):
                return f"{self.id}: leverage_limit {lev} > {ceiling}"
            return None
        if k == "stop_policy_required":
            if self.params.get("required", True) and not has_stop:
                return f"{self.id}: stop policy required"
            return None
        if k in ("no_new_risk_on_stale_data", "no_new_risk_on_unknown_execution_state"):
            # Declarative runtime gates — presence is the contract; runtime enforces later
            if not self.params.get("declared", True):
                raise SpecV2Error(f"invariant {self.id}: must be declared")
            return None
        if k == "max_open_positions":
            ceiling = self.params.get("max")
            if ceiling is None:
                raise SpecV2Error(f"invariant {self.id}: max required")
            mop = spec_risk.get("max_open_positions")
            if mop is not None and int(mop) > int(ceiling):
                return f"{self.id}: max_open_positions {mop} > {ceiling}"
            return None
        if k == "custom":
            if not self.description.strip():
                raise SpecV2Error(f"invariant {self.id}: custom requires description")
            return None
        raise SpecV2Error(f"unknown invariant kind: {k}")


class StrategyInvariants(BaseModel):
    strategy_id: str
    version: str
    rules: list[InvariantRule] = Field(default_factory=list)

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def check_spec(self, *, risk: dict[str, Any], stop_type: str) -> list[str]:
        has_stop = stop_type not in ("none", "", None)
        violations: list[str] = []
        for rule in self.rules:
            msg = rule.evaluate_against_spec(risk, has_stop=has_stop)
            if msg:
                violations.append(msg)
        return violations


def default_research_invariants(*, strategy_id: str, version: str) -> StrategyInvariants:
    return StrategyInvariants(
        strategy_id=strategy_id,
        version=version,
        rules=[
            InvariantRule(
                id="INV_NO_MARTINGALE",
                kind="no_martingale",
                description="Forbid unbounded post-loss size escalation",
                params={"forbid_types": ["martingale"]},
            ),
            InvariantRule(
                id="INV_NO_UNBOUNDED_AVG_DOWN",
                kind="no_unbounded_averaging_down",
                description="Forbid unbounded averaging down on losing positions",
                params={"max_adds_on_loss": 0},
            ),
            InvariantRule(
                id="INV_MAX_OPEN_POS",
                kind="max_open_positions",
                params={"max": 1},
                description="Default research max open positions",
            ),
            InvariantRule(
                id="INV_STALE_DATA_NO_RISK",
                kind="no_new_risk_on_stale_data",
                description="No new risk when data is stale",
                params={"declared": True},
            ),
            InvariantRule(
                id="INV_UNKNOWN_EXEC_NO_RISK",
                kind="no_new_risk_on_unknown_execution_state",
                description="No new risk when execution state is unknown",
                params={"declared": True},
            ),
        ],
    )


def validate_invariants(data: dict[str, Any] | StrategyInvariants) -> StrategyInvariants:
    if isinstance(data, StrategyInvariants):
        inv = data
    else:
        try:
            inv = StrategyInvariants.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            raise SpecV2Error(f"invalid invariants: {exc}") from exc
    if not inv.strategy_id.strip() or not inv.version.strip():
        raise SpecV2Error("invariants require strategy_id and version")
    if not inv.rules:
        raise SpecV2Error("invariants.rules must be non-empty")
    # Force param validation by evaluating against empty risk (declarative rules only)
    for rule in inv.rules:
        if rule.kind == "max_risk_per_trade" and "max" not in rule.params:
            raise SpecV2Error(f"{rule.id}: max required")
        if rule.kind == "max_leverage" and "max" not in rule.params:
            raise SpecV2Error(f"{rule.id}: max required")
        if rule.kind == "no_unbounded_averaging_down" and "max_adds_on_loss" not in rule.params:
            raise SpecV2Error(f"{rule.id}: max_adds_on_loss required")
        if rule.kind == "max_open_positions" and "max" not in rule.params:
            raise SpecV2Error(f"{rule.id}: max required")
        if rule.kind == "custom" and not rule.description.strip():
            raise SpecV2Error(f"{rule.id}: custom requires description")
    return inv

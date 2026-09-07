"""Portfolio Governor — explainable / auditable / replayable actions (no invariant bypass)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from engine.portfolio.correlation import pairwise_return_correlation
from engine.portfolio.limits import PortfolioLimits
from engine.portfolio.risk_clusters import cluster_by_correlation

ActionKind = Literal[
    "ALLOW",
    "REDUCE_WEIGHT",
    "BLOCK_ADD",
    "DE_RISK",
    "DENY_REAL_MONEY",
]


class GovernorAction(BaseModel):
    kind: ActionKind
    strategy_id: str | None = None
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)
    auditable: bool = True
    replayable: bool = True
    bypasses_invariants: bool = False


class PortfolioGovernor(BaseModel):
    limits: PortfolioLimits = Field(default_factory=PortfolioLimits)
    strategy_ids: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)
    instruments: dict[str, str] = Field(default_factory=dict)
    drawdowns: dict[str, float] = Field(default_factory=dict)


def evaluate_portfolio(
    gov: PortfolioGovernor,
    returns: dict[str, Any] | None = None,
) -> list[GovernorAction]:
    """Evaluate portfolio vs limits; never recommends real money or invariant bypass."""
    actions: list[GovernorAction] = []
    lim = gov.limits

    if lim.real_money:
        actions.append(
            GovernorAction(
                kind="DENY_REAL_MONEY",
                reason="PortfolioLimits.real_money=true is forbidden under campaign",
                details={"REAL_MONEY": "DENY"},
            )
        )

    if len(gov.strategy_ids) > lim.max_strategies:
        actions.append(
            GovernorAction(
                kind="BLOCK_ADD",
                reason=f"strategy count {len(gov.strategy_ids)} > max {lim.max_strategies}",
            )
        )

    gross = sum(abs(float(w)) for w in gov.weights.values())
    if gross > lim.max_gross_exposure + 1e-12:
        actions.append(
            GovernorAction(
                kind="DE_RISK",
                reason=f"gross exposure {gross:.4f} > {lim.max_gross_exposure}",
                details={"gross": gross},
            )
        )

    for sid, w in gov.weights.items():
        if abs(float(w)) > lim.max_per_strategy_weight + 1e-12:
            actions.append(
                GovernorAction(
                    kind="REDUCE_WEIGHT",
                    strategy_id=sid,
                    reason=f"weight {w} > max_per_strategy_weight {lim.max_per_strategy_weight}",
                )
            )

    # instrument concentration
    by_inst: dict[str, float] = {}
    for sid, w in gov.weights.items():
        inst = gov.instruments.get(sid, sid)
        by_inst[inst] = by_inst.get(inst, 0.0) + abs(float(w))
    for inst, w in by_inst.items():
        if w > lim.max_per_instrument_weight + 1e-12:
            actions.append(
                GovernorAction(
                    kind="DE_RISK",
                    reason=f"instrument {inst} weight {w:.4f} > limit",
                    details={"instrument": inst, "weight": w},
                )
            )

    for sid, dd in gov.drawdowns.items():
        # drawdowns expected negative; breach if more negative than budget
        if float(dd) < -abs(lim.max_drawdown_budget) - 1e-12:
            actions.append(
                GovernorAction(
                    kind="DE_RISK",
                    strategy_id=sid,
                    reason=f"drawdown {dd} breaches budget {lim.max_drawdown_budget}",
                    details={"drawdown": dd},
                )
            )

    if returns and len(returns) >= 2:
        corr = pairwise_return_correlation(returns)
        pairs = corr.get("pairs") or []
        for p in pairs:
            if abs(float(p["corr"])) > lim.max_pairwise_correlation + 1e-12:
                actions.append(
                    GovernorAction(
                        kind="BLOCK_ADD",
                        reason=(
                            f"correlation {p['a']}/{p['b']}={p['corr']:.3f} "
                            f"> max {lim.max_pairwise_correlation}"
                        ),
                        details=dict(p),
                    )
                )
        clusters = cluster_by_correlation(pairs, threshold=lim.max_pairwise_correlation)
        for c in clusters:
            if len(c) > lim.max_cluster_size:
                actions.append(
                    GovernorAction(
                        kind="DE_RISK",
                        reason=f"risk cluster size {len(c)} > max {lim.max_cluster_size}",
                        details={"cluster": c},
                    )
                )

    if lim.forbid_bypass_invariants:
        for a in actions:
            if a.bypasses_invariants:
                raise RuntimeError("governor action attempted invariant bypass")

    if not actions:
        actions.append(
            GovernorAction(
                kind="ALLOW",
                reason="within portfolio limits",
                details={"n_strategies": len(gov.strategy_ids), "gross": gross},
            )
        )
    return actions

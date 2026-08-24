"""QuantLab user-level risk policy (layer above Nautilus RiskEngine)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

RiskAction = Literal["ALLOW", "DENY_NEW_ENTRY", "PAUSE_STRATEGY"]


@dataclass
class PaperRiskPolicy:
    policy_id: str = "default_paper_v1"
    version: str = "v1"
    max_order_notional: float = 50_000.0
    max_position_notional: float = 100_000.0
    max_open_positions: int = 1
    max_strategy_exposure: float = 100_000.0
    daily_loss_limit: float = 5_000.0
    max_drawdown: float = 0.15
    max_consecutive_losses: int = 5
    order_rate_limit_per_minute: int = 10

    def policy_hash(self) -> str:
        from engine.paper.manifest import content_hash

        return content_hash(asdict(self))


@dataclass
class RiskEvent:
    timestamp: str
    policy: str
    code: str
    threshold: float | int | None
    observed_value: float | int | None
    action: RiskAction
    message_zh: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskEvaluation:
    allowed: bool
    action: RiskAction
    events: list[RiskEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "events": [e.to_dict() for e in self.events],
        }


def evaluate_risk(
    policy: PaperRiskPolicy,
    *,
    order_notional: float,
    position_notional: float,
    open_positions: int,
    strategy_exposure: float,
    daily_pnl: float,
    drawdown: float,
    consecutive_losses: int,
    orders_last_minute: int,
    new_entry: bool = True,
) -> RiskEvaluation:
    events: list[RiskEvent] = []
    now = datetime.now(timezone.utc).isoformat()

    def _evt(code: str, threshold, observed, action: RiskAction, msg: str) -> None:
        events.append(
            RiskEvent(
                timestamp=now,
                policy=f"{policy.policy_id}:{policy.version}",
                code=code,
                threshold=threshold,
                observed_value=observed,
                action=action,
                message_zh=msg,
            )
        )

    if new_entry and order_notional > policy.max_order_notional:
        _evt(
            "MAX_ORDER_NOTIONAL",
            policy.max_order_notional,
            order_notional,
            "DENY_NEW_ENTRY",
            f"单笔名义 {order_notional:.0f} 超过上限 {policy.max_order_notional:.0f}",
        )
    if new_entry and position_notional > policy.max_position_notional:
        _evt(
            "MAX_POSITION_NOTIONAL",
            policy.max_position_notional,
            position_notional,
            "DENY_NEW_ENTRY",
            "持仓名义超过上限",
        )
    if new_entry and open_positions >= policy.max_open_positions:
        _evt(
            "MAX_OPEN_POSITIONS",
            policy.max_open_positions,
            open_positions,
            "DENY_NEW_ENTRY",
            "已达最大持仓数",
        )
    if strategy_exposure > policy.max_strategy_exposure:
        _evt(
            "MAX_STRATEGY_EXPOSURE",
            policy.max_strategy_exposure,
            strategy_exposure,
            "DENY_NEW_ENTRY",
            "策略总敞口超限",
        )
    if daily_pnl <= -abs(policy.daily_loss_limit):
        _evt(
            "DAILY_LOSS_LIMIT_TRIGGERED",
            policy.daily_loss_limit,
            daily_pnl,
            "PAUSE_STRATEGY",
            "触发日损限制",
        )
    if drawdown >= policy.max_drawdown:
        _evt(
            "MAX_DRAWDOWN",
            policy.max_drawdown,
            drawdown,
            "PAUSE_STRATEGY",
            "触发最大回撤",
        )
    if consecutive_losses >= policy.max_consecutive_losses:
        _evt(
            "MAX_CONSECUTIVE_LOSSES",
            policy.max_consecutive_losses,
            consecutive_losses,
            "PAUSE_STRATEGY",
            "连续亏损次数超限",
        )
    if new_entry and orders_last_minute >= policy.order_rate_limit_per_minute:
        _evt(
            "ORDER_RATE_LIMIT",
            policy.order_rate_limit_per_minute,
            orders_last_minute,
            "DENY_NEW_ENTRY",
            "下单频率超限",
        )

    if not events:
        return RiskEvaluation(allowed=True, action="ALLOW")

    pause = any(e.action == "PAUSE_STRATEGY" for e in events)
    if pause:
        return RiskEvaluation(allowed=False, action="PAUSE_STRATEGY", events=events)
    return RiskEvaluation(allowed=False, action="DENY_NEW_ENTRY", events=events)

"""Liquidity / capacity checks (research-grade, not broker quotes)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CapacityLimits(BaseModel):
    max_adv_participation: float = 0.05  # fraction of ADV
    min_adv_notional: float = 1.0
    max_strategy_notional: float = 1e9


def capacity_check(
    *,
    strategy_id: str,
    desired_notional: float,
    adv_notional: float,
    limits: CapacityLimits | None = None,
) -> dict[str, Any]:
    lim = limits or CapacityLimits()
    if adv_notional < lim.min_adv_notional:
        return {
            "strategy_id": strategy_id,
            "status": "FAIL",
            "reason": "ADV below minimum",
            "adv_notional": adv_notional,
        }
    participation = abs(desired_notional) / (adv_notional + 1e-12)
    ok = participation <= lim.max_adv_participation and abs(desired_notional) <= lim.max_strategy_notional
    return {
        "strategy_id": strategy_id,
        "status": "PASS" if ok else "FAIL",
        "participation": participation,
        "desired_notional": desired_notional,
        "adv_notional": adv_notional,
        "reason": None if ok else "capacity / participation breach",
    }

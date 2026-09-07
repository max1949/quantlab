"""Shadow Twin — compare paper/reference vs shadow stream for divergence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


DivergenceKind = Literal["SIGNAL", "ORDER", "POSITION", "NONE"]


class ShadowSnapshot(BaseModel):
    ts: str
    strategy_id: str
    signal: float | None = None
    order_side: str | None = None
    position: float = 0.0
    price: float | None = None
    source: str = "shadow"


class DivergenceEvent(BaseModel):
    kind: DivergenceKind
    strategy_id: str
    ts: str
    reference: dict[str, Any] = Field(default_factory=dict)
    shadow: dict[str, Any] = Field(default_factory=dict)
    detail: str = ""


def compare_twins(
    reference: ShadowSnapshot,
    shadow: ShadowSnapshot,
    *,
    signal_eps: float = 1e-9,
    position_eps: float = 1e-9,
) -> list[DivergenceEvent]:
    """Detect signal/order/position divergence between reference and shadow."""
    if reference.strategy_id != shadow.strategy_id:
        raise ValueError("strategy_id mismatch")
    events: list[DivergenceEvent] = []
    ts = shadow.ts or reference.ts
    if reference.signal is not None and shadow.signal is not None:
        if abs(float(reference.signal) - float(shadow.signal)) > signal_eps:
            events.append(
                DivergenceEvent(
                    kind="SIGNAL",
                    strategy_id=reference.strategy_id,
                    ts=ts,
                    reference={"signal": reference.signal},
                    shadow={"signal": shadow.signal},
                    detail="signal divergence",
                )
            )
    if (reference.order_side or None) != (shadow.order_side or None):
        events.append(
            DivergenceEvent(
                kind="ORDER",
                strategy_id=reference.strategy_id,
                ts=ts,
                reference={"order_side": reference.order_side},
                shadow={"order_side": shadow.order_side},
                detail="order side divergence",
            )
        )
    if abs(float(reference.position) - float(shadow.position)) > position_eps:
        events.append(
            DivergenceEvent(
                kind="POSITION",
                strategy_id=reference.strategy_id,
                ts=ts,
                reference={"position": reference.position},
                shadow={"position": shadow.position},
                detail="position divergence",
            )
        )
    if not events:
        events.append(
            DivergenceEvent(
                kind="NONE",
                strategy_id=reference.strategy_id,
                ts=ts,
                detail="twins agree",
            )
        )
    return events

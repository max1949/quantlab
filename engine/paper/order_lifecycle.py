"""Order lifecycle state machine for paper sandbox."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class OrderLifecycleState(str, Enum):
    INITIALIZED = "OrderInitialized"
    SUBMITTED = "OrderSubmitted"
    ACCEPTED = "OrderAccepted"
    FILLED = "OrderFilled"
    REJECTED = "Rejected"
    CANCELED = "Canceled"
    EXPIRED = "Expired"
    PARTIAL = "PartialFill"


@dataclass
class LifecycleEvent:
    event_type: str
    timestamp: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaperOrderState:
    order_id: str
    instrument: str
    side: str
    quantity: float
    price: float | None = None
    state: OrderLifecycleState = OrderLifecycleState.INITIALIZED
    events: list[LifecycleEvent] = field(default_factory=list)
    filled_quantity: float = 0.0
    fee: float = 0.0

    def _emit(self, event_type: str, **detail: Any) -> None:
        self.events.append(
            LifecycleEvent(
                event_type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                detail=detail,
            )
        )

    def submit(self) -> None:
        self.state = OrderLifecycleState.SUBMITTED
        self._emit("OrderSubmitted")

    def accept(self) -> None:
        self.state = OrderLifecycleState.ACCEPTED
        self._emit("OrderAccepted")

    def fill(self, *, price: float, quantity: float | None = None, fee: float = 0.0) -> None:
        qty = quantity if quantity is not None else self.quantity
        self.filled_quantity += qty
        self.price = price
        self.fee += fee
        if self.filled_quantity >= self.quantity:
            self.state = OrderLifecycleState.FILLED
            self._emit("OrderFilled", price=price, quantity=qty, fee=fee)
        else:
            self.state = OrderLifecycleState.PARTIAL
            self._emit("PartialFill", price=price, quantity=qty, fee=fee)

    def reject(self, reason: str) -> None:
        self.state = OrderLifecycleState.REJECTED
        self._emit("Rejected", reason=reason)

    def cancel(self) -> None:
        self.state = OrderLifecycleState.CANCELED
        self._emit("Canceled")

    def expire(self) -> None:
        self.state = OrderLifecycleState.EXPIRED
        self._emit("Expired")


def create_market_order(
    *,
    instrument: str,
    side: str,
    quantity: float,
) -> PaperOrderState:
    order = PaperOrderState(
        order_id=str(uuid.uuid4()),
        instrument=instrument,
        side=side,
        quantity=quantity,
    )
    order._emit("OrderInitialized", side=side, quantity=quantity)
    return order

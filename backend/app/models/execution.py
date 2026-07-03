"""模拟执行 / 纸面下单 — 机构级执行适配层 v0。"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    FILLED = "filled"
    PENDING = "pending"
    ROUTED = "routed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PaperOrder(Base):
    __tablename__ = "paper_orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    factor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("factors.id", ondelete="SET NULL"), index=True, nullable=True
    )
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    notional_cny: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=OrderStatus.FILLED.value)
    signal_value: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    regime: Mapped[str | None] = mapped_column(String(8), nullable=True)
    regime_fit_score: Mapped[int | None] = mapped_column(nullable=True)
    channel: Mapped[str] = mapped_column(String(16), nullable=False, default="paper")
    external_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    risk_verdict: Mapped[str] = mapped_column(String(16), nullable=False, default="passed")
    risk_detail: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    gateway_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    routed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PaperOrderEvent(Base):
    __tablename__ = "paper_order_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("paper_orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    gateway_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    detail: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

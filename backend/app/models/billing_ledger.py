"""机构 / 个人计费流水 (发票级审计)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class BillingLedger(Base):
    __tablename__ = "billing_ledger"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)  # org | personal
    event: Mapped[str] = mapped_column(String(20), nullable=False)  # redeem | checkout | grant
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("research_orgs.id", ondelete="SET NULL"), index=True, nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False)
    plan_name: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    tier: Mapped[int] = mapped_column(nullable=False, default=0)
    seats: Mapped[int | None] = mapped_column(nullable=True)
    amount_cny: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="redeem")
    stripe_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    subscription_ref: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detail: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

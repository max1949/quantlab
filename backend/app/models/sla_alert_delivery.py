"""SLA 告警 Webhook 投递审计 (机构运维)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.core.database import Base


class SlaAlertDelivery(Base):
    __tablename__ = "sla_alert_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scope: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("research_orgs.id", ondelete="SET NULL"), index=True, nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trigger: Mapped[str] = mapped_column(String(16), nullable=False, default="scheduled")
    alert_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    retry_of_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("sla_alert_deliveries.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

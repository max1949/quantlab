"""因子参数扫描实验记录。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.core.database import Base


class FactorScan(Base):
    __tablename__ = "factor_scans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("research_projects.id", ondelete="SET NULL"), index=True, nullable=True
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False, default="1d")
    template_type: Mapped[str] = mapped_column(String(64), nullable=False)
    results: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    best_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    best_score: Mapped[float | None] = mapped_column(nullable=True)
    coach_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    applied_factor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("factors.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

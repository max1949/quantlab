"""纸面跟踪快照 (每日因子 NAV 记录)。"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class PaperSnapshot(Base):
    """因子在某交易日的纸面跟踪快照 (验证通过后自动记录)。"""

    __tablename__ = "paper_snapshots"
    __table_args__ = (
        UniqueConstraint("factor_id", "as_of_date", name="uq_paper_factor_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    factor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("factors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), server_default="1d", nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    bars: Mapped[int] = mapped_column(Integer, nullable=False)
    nav_end: Mapped[float] = mapped_column(Float, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    equity_tail: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

"""研究项目报告模型 (Sprint 8.1)。

把一个因子的研究全过程聚合成一篇可留存、可公开展示的叙事报告。
是"研究生态"的核心数据资产 (后续研究员主页/社区基于它统计与展示)。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class ResearchReport(Base):
    """一篇自动生成的研究项目报告。"""

    __tablename__ = "research_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    factor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("factors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    grade: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # 研究阶段完成度 {factor, backtest, validation}
    stages: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # 完整叙事 (sections + markdown)
    narrative: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # 溯源: {backtest_id, validation_id}
    based_on: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

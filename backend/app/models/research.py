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
    Integer,
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
    # 所属研究项目 (Sprint 8); 可空 -> 兼容因子级独立报告。
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("research_projects.id", ondelete="SET NULL"), index=True, nullable=True
    )
    factor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("factors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # 因子版本快照 (factor.version), 保证报告可复现。
    factor_version: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # 结构化报告字段 (与 narrative 一致, 便于直接展示/检索)。
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    methodology: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result: Mapped[str] = mapped_column(Text, nullable=False, default="")
    risk_analysis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    improvement_suggestion: Mapped[str] = mapped_column(Text, nullable=False, default="")
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

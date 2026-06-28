"""成长挑战 (Sprint 8): 30 天研究挑战。

把零散的成长任务编排成一条有节奏的旅程 (Day1 第一个因子 → Day7 首次 OOS →
Day15 组合因子 → Day30 研究报告), 给小白明确的"下一步该做什么", 驱动留存。

里程碑用"可自动判定"的条件 (统计用户产物), 不需手动打卡。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class Challenge(Base):
    """挑战定义 (平台预置)。"""

    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    days: Mapped[int] = mapped_column(Integer, default=30, server_default="30", nullable=False)
    # 里程碑列表: [{day, code, title, check, reward_points}], check 为自动判定条件键。
    milestones: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # 可选: 限定给某分流身份 (Sprint 9); 空=通用。
    user_type: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ChallengeProgress(Base):
    """用户在某挑战上的进度。"""

    __tablename__ = "challenge_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_challenge_progress"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("challenges.id", ondelete="CASCADE"), index=True, nullable=False
    )
    completed: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # 里程碑 code 列表
    # 已发放奖励的里程碑 code (防重复发奖)。
    rewarded: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # 全部完成时生成的证书编号 (可空 -> 未完成)。
    certificate_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

"""竞技系统模型 (Sprint 6): 赛季 + 提交。

研究员把"已通过科学验证"的因子提交到赛季, 平台用 Research Score (五维 + 动态衰减)
打分并排名。强调研究质量与稳健性, 而非单纯收益。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class SeasonStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class Season(Base):
    """竞赛赛季。"""

    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(16), default=SeasonStatus.OPEN.value, server_default="open", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Submission(Base):
    """一次赛季提交及其 Research Score 明细。"""

    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("season_id", "validation_id", name="uq_submission_season_validation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("seasons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    factor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("factors.id", ondelete="CASCADE"), nullable=False
    )
    validation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("validations.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)

    base_score: Mapped[float] = mapped_column(Float, nullable=False)
    decay_factor: Mapped[float] = mapped_column(Float, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    dimensions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

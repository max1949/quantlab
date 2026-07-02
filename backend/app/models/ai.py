"""AI 研究助手产物 (Sprint 7)。

每次生成 (验证复盘 / 回测总结) 落一条记录, 保存最终文本 + 结构化本地分析 + 来源
(llm / local) + 模型名, 既可追溯也方便"我的洞察"列表回看。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class InsightKind(str, enum.Enum):
    VALIDATION_REVIEW = "validation_review"
    BACKTEST_SUMMARY = "backtest_summary"
    SCAN_REVIEW = "scan_review"


class InsightSource(str, enum.Enum):
    LLM = "llm"
    LOCAL = "local"


class AiInsight(Base):
    """一次 AI 生成的研究洞察。"""

    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    # 关联对象 (validation / backtest) 的类型与 id。
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)

    source: Mapped[str] = mapped_column(String(16), nullable=False)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    analysis: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

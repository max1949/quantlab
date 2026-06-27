"""AI 研究助手 schema (Sprint 7)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AiStatusOut(BaseModel):
    enabled: bool          # 是否已接入外部 LLM (否则走本地规则分析)
    model: str | None      # 启用时的模型名
    fallback: str = "local"  # 降级方式说明


class InsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    target_type: str
    target_id: uuid.UUID
    source: str            # llm | local
    model: str | None
    content: str           # 最终自然语言回复 (markdown)
    analysis: dict         # 结构化本地分析
    created_at: datetime

"""研究项目报告 schema (Sprint 8.1)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportSummary(BaseModel):
    """列表用精简视图。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    factor_id: uuid.UUID
    symbol: str
    title: str
    grade: str | None
    stages: dict
    is_public: bool
    created_at: datetime


class ReportDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    factor_id: uuid.UUID
    symbol: str
    title: str
    hypothesis: str
    grade: str | None
    stages: dict
    narrative: dict
    based_on: dict
    is_public: bool
    created_at: datetime

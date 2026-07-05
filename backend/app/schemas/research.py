"""研究项目报告 schema (Sprint 8.1)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.growth import MasteryPathSnapshotOut
from backend.app.schemas.task import AcademyRewardOut


class ReportSummary(BaseModel):
    """列表/Feed 用精简视图。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    project_id: uuid.UUID | None
    factor_id: uuid.UUID
    symbol: str
    title: str
    grade: str | None
    stages: dict
    is_public: bool
    created_at: datetime
    oos_sharpe: float | None = None
    robustness_score: float | None = None
    factor_kind: str | None = None
    factor_template: str | None = None
    timeframe: str | None = None
    paper_graduated: bool = False
    paper_tracking: bool = False
    mastery_badge: str | None = None
    mastery_path: MasteryPathSnapshotOut | None = None
    owner_username: str | None = None
    is_following: bool | None = None


class ReportDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    project_id: uuid.UUID | None
    factor_id: uuid.UUID
    factor_version: int
    symbol: str
    title: str
    summary: str
    hypothesis: str
    methodology: str
    result: str
    risk_analysis: str
    improvement_suggestion: str
    grade: str | None
    stages: dict
    narrative: dict
    based_on: dict
    is_public: bool
    created_at: datetime
    academy_rewards: list[AcademyRewardOut] = Field(default_factory=list)


class GenerateReportRequest(BaseModel):
    """二选一: 传 project_id 生成项目报告, 或 factor_id 生成因子报告。"""

    project_id: uuid.UUID | None = None
    factor_id: uuid.UUID | None = None


class ShareCreateIn(BaseModel):
    """分享卡片创建参数 — replication_loop 表示大师复现闭环分享。"""

    replication_loop: bool = False

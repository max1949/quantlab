"""研究员主页 schema (Sprint 8)。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ResearcherProfile(BaseModel):
    user_id: str
    username: str
    level: int
    level_label: str
    research_score: float
    experience: int
    project_count: int
    factor_count: int
    validation_count: int
    effective_validation_count: int
    report_count: int
    tags: list[str]
    joined_at: datetime

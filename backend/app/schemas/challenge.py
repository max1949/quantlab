"""30 天挑战 schema (Sprint 8)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChallengeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    description: str
    days: int
    milestones: list


class MilestoneStatus(BaseModel):
    day: int
    code: str
    title: str
    completed: bool


class ProgressOut(BaseModel):
    code: str
    title: str
    days: int
    completed_count: int
    total: int
    percent: float
    milestones: list[MilestoneStatus]
    enrolled_at: datetime

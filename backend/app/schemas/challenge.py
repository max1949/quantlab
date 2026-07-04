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
    reward_points: int = 0
    journey_key: str | None = None
    journey_label: str | None = None
    mastery_stage: str | None = None
    mastery_stage_label: str | None = None


class ProgressOut(BaseModel):
    code: str
    title: str
    days: int
    completed_count: int
    total: int
    percent: float
    milestones: list[MilestoneStatus]
    enrolled_at: datetime
    newly_awarded_points: int = 0
    reward_points: int = 0
    certificate_code: str | None = None
    completed_at: datetime | None = None


class CertificateOut(BaseModel):
    certificate_code: str
    challenge_title: str
    username: str
    completed_at: datetime | None

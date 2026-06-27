"""竞技系统出入参 schema (Sprint 6)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SeasonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = ""


class SeasonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    status: str
    created_at: datetime


class SubmissionCreate(BaseModel):
    validation_id: uuid.UUID


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    season_id: uuid.UUID
    owner_id: uuid.UUID
    factor_id: uuid.UUID
    validation_id: uuid.UUID
    symbol: str
    base_score: float
    decay_factor: float
    final_score: float
    dimensions: dict
    created_at: datetime


class LeaderboardRow(BaseModel):
    rank: int
    username: str
    factor_id: uuid.UUID
    symbol: str
    base_score: float
    decay_factor: float
    final_score: float
    submitted_at: datetime

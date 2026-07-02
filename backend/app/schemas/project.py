"""研究项目 + 图谱 schema (Sprint 8)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.task import AcademyRewardOut


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    symbol: str = Field(default="", max_length=32)
    question: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    symbol: str
    question: str
    description: str
    status: str
    tags: list
    created_at: datetime
    updated_at: datetime


class PublishProjectOut(ProjectOut):
    academy_rewards: list[AcademyRewardOut] = Field(default_factory=list)


class GraphNodeOut(BaseModel):
    id: str
    kind: str
    label: str
    ref_type: str | None
    ref_id: str | None
    detail: dict
    order: int


class GraphEdgeOut(BaseModel):
    from_: str = Field(alias="from")
    to: str
    label: str

    model_config = ConfigDict(populate_by_name=True)


class GraphOut(BaseModel):
    project_id: str
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]

"""schemas for research organizations."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrgCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class OrgMemberAdd(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class OrgFactorShareIn(BaseModel):
    note: str = Field(default="", max_length=500)


class OrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    created_at: datetime
    member_count: int = 0
    shared_factor_count: int = 0
    my_role: str | None = None


class OrgMemberOut(BaseModel):
    user_id: uuid.UUID
    username: str
    role: str
    joined_at: datetime


class OrgFactorShareOut(BaseModel):
    factor_id: uuid.UUID
    factor_name: str
    owner_username: str
    kind: str
    note: str
    shared_at: datetime

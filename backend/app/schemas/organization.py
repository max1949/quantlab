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


class OrgMemberUpdate(BaseModel):
    role: str = Field(pattern=r"^(admin|member|viewer)$")


class OrgInviteCreate(BaseModel):
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")
    expires_in_days: int = Field(default=7, ge=1, le=90)
    max_uses: int = Field(default=1, ge=1, le=200)


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


class OrgInviteOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    org_name: str
    token: str
    role: str
    max_uses: int
    used_count: int
    expires_at: datetime
    created_at: datetime
    invite_path: str


class OrgInvitePreviewOut(BaseModel):
    org_id: uuid.UUID
    org_name: str
    role: str
    expires_at: datetime
    used_count: int
    max_uses: int
    already_member: bool


class OrgInviteListOut(OrgInviteOut):
    active: bool


class OrgActivityOut(BaseModel):
    id: str
    action: str
    actor_id: str | None
    resource_type: str
    resource_id: str
    detail: dict
    created_at: str


class OrgBillingOut(BaseModel):
    org_id: uuid.UUID
    org_name: str
    tier: int
    tier_name: str
    plan_code: str
    expires_at: datetime | None
    seats: int
    member_count: int
    is_paid: bool
    team_plans: list[dict]


class OrgBillingRedeemIn(BaseModel):
    code: str


class OrgBillingRedeemOut(BaseModel):
    ok: bool
    tier: int
    tier_name: str
    expires_at: datetime | None
    seats: int
    message: str

"""用户系统的出入参 schema。

入参做基础校验 (邮箱格式 / 用户名规则 / 密码长度);
出参绝不暴露 ``hashed_password`` 等敏感字段。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from backend.app.models.user import UserLevel


class UserCreate(BaseModel):
    """注册入参。"""

    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_]+$",
        description="字母 / 数字 / 下划线, 3-50 位",
    )
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """登录入参 (支持邮箱或用户名)。"""

    identifier: str = Field(description="邮箱或用户名")
    password: str


class UserOut(BaseModel):
    """用户出参 (公开安全字段)。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    level: int
    experience: int
    research_score: float
    is_active: bool
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def level_label(self) -> str:
        return UserLevel(self.level).label

    @computed_field  # type: ignore[prop-decorator]
    @property
    def experience_to_next_level(self) -> int | None:
        # 延迟导入避免循环依赖 (leveling 依赖 models.user)。
        from backend.app.services.leveling import experience_to_next_level

        return experience_to_next_level(self.experience)


class Token(BaseModel):
    """令牌出参。"""

    access_token: str
    token_type: str = "bearer"

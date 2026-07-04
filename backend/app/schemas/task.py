"""学院任务的出入参 schema (Sprint 2)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from backend.app.models.user import UserLevel
from backend.app.schemas.user import UserOut


class TaskOut(BaseModel):
    """任务基础信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    description: str
    category: str
    min_level: int
    xp_reward: int
    order_index: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def min_level_label(self) -> str:
        return UserLevel(self.min_level).label


class TaskWithProgress(TaskOut):
    """任务 + 当前用户的进度状态 (列表/详情用)。"""

    completed: bool
    locked: bool  # 当前用户等级 < min_level
    completed_at: datetime | None = None
    mastery_stage: str | None = None


class CompleteTaskResult(BaseModel):
    """完成任务的结果: 奖励 / 是否升级 / 最新用户状态。"""

    task: TaskOut
    awarded_xp: int
    leveled_up: bool
    previous_level: int
    user: UserOut


class AcademyRewardOut(BaseModel):
    code: str
    title: str
    awarded_xp: int
    leveled_up: bool

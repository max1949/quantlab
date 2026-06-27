"""学院任务 (Academy) 模型 —— Sprint 2。

`Task`: 平台预置的成长任务 (任务驱动把观察员培养为研究员)。
`UserTask`: 用户与任务的完成关系 (谁完成了哪个任务、何时)。

等级绑定权限体现在 `Task.min_level`: 低于该等级的用户看到的是"锁定"任务,
不能完成 (服务层抛 403)。完成任务奖励 `xp_reward` 经验, 经验累计驱动升级。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.core.database import Base
from backend.app.models.user import UserLevel


class TaskStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Task(Base):
    """预置成长任务。"""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    # 稳定业务编码 (种子/迁移引用用, 不随主键变化)。
    code: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="onboarding"
    )

    # 解锁所需最低等级 (等级绑定权限)。
    min_level: Mapped[int] = mapped_column(
        SmallInteger, default=UserLevel.L0.value, server_default="0", nullable=False
    )
    # 完成奖励经验。
    xp_reward: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    # 展示排序。
    order_index: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserTask(Base):
    """用户完成任务的记录。"""

    __tablename__ = "user_tasks"
    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="uq_user_task"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.COMPLETED.value, nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    task: Mapped[Task] = relationship(lazy="joined")

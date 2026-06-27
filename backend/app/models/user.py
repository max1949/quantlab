"""User ORM 模型。

Sprint 1 用户系统的核心实体。等级 (Level) 是平台的能力闸门:
Level 决定用户能做什么 (L0 模板 → L1 组合器 → L2 Python → L3 vn.py),
等级绑定权限的校验逻辑在 Sprint 2 (学院系统) 展开,这里先把字段与语义定下来。

`research_score` 为研究积分预留 (Sprint 6 竞技系统使用动态评分),
放在 User 上是因为它属于研究员的长期身份属性,提前建好可避免后续迁移抖动。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class UserLevel(enum.IntEnum):
    """研究员等级。

    用 IntEnum 是为了让权限判断退化为简单的数值比较 (``level >= required``),
    既能表达"能力随等级单调增长",也便于排序与展示。
    """

    L0 = 0  # 观察员: 只读 + 模板因子
    L1 = 1  # 研究学徒: 因子组合器
    L2 = 2  # 研究员: 自定义 Python 因子 (沙箱执行)
    L3 = 3  # 高级研究员: vn.py 模拟/实盘接口

    @property
    def label(self) -> str:
        return {
            UserLevel.L0: "观察员",
            UserLevel.L1: "研究学徒",
            UserLevel.L2: "研究员",
            UserLevel.L3: "高级研究员",
        }[self]


class User(Base):
    """平台用户 / 研究员。"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # 等级: 平台能力闸门 (默认 L0 观察员)。存为 SmallInteger,语义见 UserLevel。
    level: Mapped[int] = mapped_column(
        SmallInteger, default=UserLevel.L0.value, server_default="0", nullable=False
    )

    # 研究积分: Sprint 6 动态评分写入,这里仅占位 (默认 0)。
    research_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def user_level(self) -> UserLevel:
        return UserLevel(self.level)

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"<User {self.username} L{self.level}>"

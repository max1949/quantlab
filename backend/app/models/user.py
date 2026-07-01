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

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    func,
)
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
    L2 = 2  # 研究员: 自定义公式因子 + 截面回测 + 成本敏感性
    L3 = 3  # 进阶研究员: 多因子正交化 + 稳健性 + 过拟合检查
    L4 = 4  # 量化研究员(准职业): 组合优化 + 模拟实盘

    @property
    def label(self) -> str:
        return {
            UserLevel.L0: "观察员",
            UserLevel.L1: "研究学徒",
            UserLevel.L2: "研究员",
            UserLevel.L3: "进阶研究员",
            UserLevel.L4: "量化研究员",
        }[self]


class UserType(str, enum.Enum):
    """新用户分流身份 (Sprint 9): 决定 onboarding 路线与默认节奏。"""

    NEWBIE = "newbie"   # 完全新手 (从模板因子起步)
    PYTHON = "python"   # 有 Python 基础
    TRADER = "trader"   # 有交易经验

    @property
    def label(self) -> str:
        return {
            UserType.NEWBIE: "完全新手",
            UserType.PYTHON: "Python 用户",
            UserType.TRADER: "交易经验用户",
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
    # 由 experience 经阈值推导 (见 services/leveling.py), 完成任务后更新。
    level: Mapped[int] = mapped_column(
        SmallInteger, default=UserLevel.L0.value, server_default="0", nullable=False
    )

    # 累计经验值: 学院任务成长的核心计数器 (Sprint 2)。单调递增。
    experience: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    # 研究积分 (Sprint 6 竞技): 历史最佳 Research Score (五维×衰减), 竞技身份指标。
    research_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )

    # --- Sprint 9 Growth OS: 两套互不合并的分数 ---
    # reward_points: 游戏化激励积分 (完成里程碑/邀请/分享等行为奖励), 可涨不沉淀研究质量。
    reward_points: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    # research_contribution_score: 长期研究信用 (由真实研究产物质量沉淀), 不被游戏行为稀释。
    research_contribution_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )

    # 分流身份 (Sprint 9): 决定 onboarding 路线。
    user_type: Mapped[str] = mapped_column(
        String(16), default=UserType.NEWBIE.value, server_default="newbie", nullable=False
    )
    onboarding_done: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    # 邀请人 (Sprint 9 裂变); 可空。
    referred_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
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

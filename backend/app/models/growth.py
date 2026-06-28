"""Growth OS 模型 (Sprint 9A): 邀请裂变 / 研究模板 / 分享卡片 / 关注 / 埋点。

这些表承载"增长层": 把研究行为转化为获取-激活-留存-传播的循环, 与研究引擎解耦。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class ReferralStatus(str, enum.Enum):
    PENDING = "pending"        # 邀请码已生成, 还没人用
    REGISTERED = "registered"  # 被邀请者已注册
    ACTIVATED = "activated"    # 被邀请者完成首次研究 -> 发奖


class Referral(Base):
    """邀请裂变 (每个被邀请者一条)。

    邀请码 = 邀请人的 username (已唯一, 小白易于分享 ``/?ref=alice``), 因此无需单独存码。
    被邀请者注册时建行 (status=registered); 完成首次研究后激活 (status=activated) 并给邀请人发奖。
    """

    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    invitee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), default=ReferralStatus.REGISTERED.value, server_default="registered", nullable=False
    )
    reward_points: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ResearchTemplate(Base):
    """研究模板 (平台预置): 一键创建研究项目 + 默认因子。"""

    __tablename__ = "research_templates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    factor_template: Mapped[str] = mapped_column(String(32), nullable=False)
    default_params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ResearchShare(Base):
    """研究分享卡片: 公开可转发链接 /share/{token} 的数据快照。"""

    __tablename__ = "research_shares"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("research_reports.id", ondelete="CASCADE"), index=True, nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    card: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    views: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserFollow(Base):
    """关注关系 (follower -> followee)。"""

    __tablename__ = "user_follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "followee_id", name="uq_user_follow"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    follower_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    followee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserEvent(Base):
    """埋点事件 (Sprint 9): 用于增长漏斗分析。user_id 可空 -> 支持匿名访客。"""

    __tablename__ = "user_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    event: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    props: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

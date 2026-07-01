"""会员 / 付费订阅模型 (Sprint 10 商业化)。

设计两条独立的闸门, 互不替代:
  - **等级 (UserLevel)**: 靠做研究"练"出来的能力闸门 (L0..L4)。
  - **会员档位 (tier)**: 用钱解锁的工具档位 (0 免费 / 1 研究员月卡 / 2 专业月卡)。

某个高级功能是否可用 = 用户等级 >= 功能要求等级 且 会员档位 >= 功能要求档位。
即: 既要练到那个段位, 也要订阅对应的卡。

真实收款 (微信支付/支付宝/Stripe) 需要商户号; 这里先用兑换码 + 可插拔的
checkout 适配层, 商户号到位后接上即可。订阅是"叠加生效", 当前档位取所有
未过期订阅里的最大 tier。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(Base):
    """一条会员订阅记录 (一次购买/兑换/赠送)。"""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False)
    # 档位: 0 免费 / 1 研究员月卡 / 2 专业月卡
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=SubscriptionStatus.ACTIVE.value,
        server_default="active",
    )
    # 来源: redeem(兑换码) / checkout(支付) / admin(后台赠送)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="redeem")

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # 到期时间; 为空表示永久 (例如内部赠送)。
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RedeemCode(Base):
    """兑换码: 在没接真实支付前, 用于发放/测试会员; 也可做促销码。"""

    __tablename__ = "redeem_codes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False, default="plus_monthly")

    used_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

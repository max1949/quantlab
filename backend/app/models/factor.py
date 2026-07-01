"""因子模型 (因子实验室, Sprint 3)。

一个 `Factor` 是用户创建的因子定义, 两类:
  - template: 由平台模板因子 + 参数实例化 (L0 即可)。
  - stack:    因子组合器, 把已有因子按权重线性组合 (需 L1, 等级绑定权限)。

设计原则"一切研究皆可复现": 保留 `version` 与不可变的 `spec`(JSON 定义),
为 Sprint 4 回测绑定因子版本/数据快照预留。
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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class FactorKind(str, enum.Enum):
    TEMPLATE = "template"
    STACK = "stack"
    FORMULA = "formula"  # L2: 用户自定义表达式因子
    PYTHON = "python"  # L3: 用户 Python 因子 (沙箱)


class Factor(Base):
    """用户创建的因子定义。"""

    __tablename__ = "factors"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_factor_owner_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # 所属研究项目 (Sprint 8); 可空 -> 兼容未归入项目的独立因子。
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("research_projects.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)

    # 模板因子: 模板编码 (momentum / rsi / ...); 组合器为 None。
    template_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 定义 JSON:
    #   template -> {"params": {...}}
    #   stack    -> {"components": [{"factor_id": "...", "weight": 0.5}, ...]}
    spec: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    version: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
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

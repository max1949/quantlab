"""研究项目与研究路径图谱 (Sprint 8)。

`ResearchProject`: 研究的顶层容器 = 一个研究主题 (如"黄金趋势是否延续")。
用户先建项目, 在项目下造因子 → 回测 → 验证 → 报告 → 发布, 形成 Research OS 闭环。

`ResearchNode` / `ResearchEdge`: 研究路径图谱, 记录"假设 → 实验 → 失败 → 优化 → 结果"
的研究轨迹, 把"过程 > 结果"沉淀成可视化的数据资产。
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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"        # 草稿: 刚建, 还没研究产物
    ACTIVE = "active"      # 进行中: 已有因子/回测/验证
    PUBLISHED = "published"  # 已发布: 公开到研究 Feed


class NodeKind(str, enum.Enum):
    HYPOTHESIS = "hypothesis"     # 研究假设
    EXPERIMENT = "experiment"     # 实验 (因子/回测)
    VALIDATION = "validation"     # 科学验证
    RESULT = "result"             # 结果 (报告)
    OPTIMIZATION = "optimization"  # 优化迭代


class ResearchProject(Base):
    """研究项目 (顶层容器)。"""

    __tablename__ = "research_projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    # 研究问题, 如"黄金趋势是否具有延续性?"
    question: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(16), default=ProjectStatus.DRAFT.value, server_default="draft", nullable=False
    )
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ResearchNode(Base):
    """研究路径节点。"""

    __tablename__ = "research_nodes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("research_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    # 关联的业务对象 (factor/backtest/validation/report), 可空。
    ref_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ref_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    order_index: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ResearchEdge(Base):
    """研究路径有向边 (from → to)。"""

    __tablename__ = "research_edges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("research_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_node: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("research_nodes.id", ondelete="CASCADE"), nullable=False
    )
    to_node: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("research_nodes.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

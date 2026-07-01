"""研究项目业务逻辑 (Sprint 8)。

项目是 Research OS 的顶层容器。本服务负责: 项目 CRUD、发布、以及由项目下的研究产物
(因子 → 回测 → 验证 → 报告) **物化研究路径图谱** (nodes/edges), 把研究过程可视化。
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.project import (
    NodeKind,
    ProjectStatus,
    ResearchEdge,
    ResearchNode,
    ResearchProject,
)
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus


class ProjectNotFoundError(Exception):
    pass


class ProjectNotPublishableError(Exception):
    """项目尚无任何研究产物, 不能发布。"""


class ProjectQualityRejectedError(Exception):
    """研究质量未达发布门槛。"""

    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


def create_project(
    db: Session, owner: User, title: str, symbol: str = "", question: str = "",
    description: str = "", tags: list | None = None,
) -> ResearchProject:
    project = ResearchProject(
        owner_id=owner.id,
        title=title,
        symbol=symbol or "",
        question=question or "",
        description=description or "",
        tags=tags or [],
        status=ProjectStatus.DRAFT.value,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: uuid.UUID) -> ResearchProject:
    p = db.get(ResearchProject, project_id)
    if p is None:
        raise ProjectNotFoundError(str(project_id))
    return p


def get_owned_project(db: Session, owner_id: uuid.UUID, project_id: uuid.UUID) -> ResearchProject:
    p = get_project(db, project_id)
    if p.owner_id != owner_id:
        raise ProjectNotFoundError(str(project_id))
    return p


def list_my_projects(db: Session, owner_id: uuid.UUID, limit: int = 100) -> list[ResearchProject]:
    return list(
        db.execute(
            select(ResearchProject)
            .where(ResearchProject.owner_id == owner_id)
            .order_by(ResearchProject.created_at.desc())
            .limit(limit)
        ).scalars().all()
    )


def _project_factor_ids(db: Session, project_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        db.execute(select(Factor.id).where(Factor.project_id == project_id)).scalars().all()
    )


def _has_artifacts(db: Session, project_id: uuid.UUID) -> bool:
    return bool(_project_factor_ids(db, project_id))


def publish_project(db: Session, owner_id: uuid.UUID, project_id: uuid.UUID) -> ResearchProject:
    from backend.app.services import research_quality_service as rq

    p = get_owned_project(db, owner_id, project_id)
    if not _has_artifacts(db, project_id):
        raise ProjectNotPublishableError(str(project_id))
    verdict = rq.assess_project(db, project_id)
    if not verdict.passed:
        raise ProjectQualityRejectedError(verdict.reasons)
    p.status = ProjectStatus.PUBLISHED.value
    db.commit()
    db.refresh(p)
    return p


def touch_active(db: Session, project_id: uuid.UUID) -> None:
    """有产物后把 draft 推进到 active (幂等)。"""
    p = db.get(ResearchProject, project_id)
    if p and p.status == ProjectStatus.DRAFT.value:
        p.status = ProjectStatus.ACTIVE.value
        db.commit()


# --------------------------------------------------------------------------- #
# 研究路径图谱: 由项目产物物化 nodes/edges (每次重建, 幂等)
# --------------------------------------------------------------------------- #

def build_graph(db: Session, project: ResearchProject) -> dict:
    db.execute(delete(ResearchEdge).where(ResearchEdge.project_id == project.id))
    db.execute(delete(ResearchNode).where(ResearchNode.project_id == project.id))
    db.flush()

    nodes: list[ResearchNode] = []
    edges: list[ResearchEdge] = []
    order = 0

    def add_node(kind, label, ref_type=None, ref_id=None, detail=None):
        nonlocal order
        n = ResearchNode(
            project_id=project.id, kind=kind, label=label,
            ref_type=ref_type, ref_id=ref_id, detail=detail or {}, order_index=order,
        )
        order += 1
        db.add(n)
        db.flush()
        nodes.append(n)
        return n

    def add_edge(a: ResearchNode, b: ResearchNode, label=""):
        e = ResearchEdge(project_id=project.id, from_node=a.id, to_node=b.id, label=label)
        db.add(e)
        edges.append(e)
        return e

    root = add_node(
        NodeKind.HYPOTHESIS.value,
        project.question or f"{project.symbol} 研究假设",
        detail={"symbol": project.symbol},
    )

    factors = list(
        db.execute(
            select(Factor).where(Factor.project_id == project.id).order_by(Factor.created_at.asc())
        ).scalars().all()
    )
    last_terminal = root
    for f in factors:
        fn = add_node(NodeKind.EXPERIMENT.value, f"因子: {f.name}", "factor", f.id)
        add_edge(root, fn, "提出")
        chain_tail = fn

        bt = db.execute(
            select(Backtest).where(
                Backtest.factor_id == f.id, Backtest.status == BacktestStatus.SUCCESS.value
            ).order_by(Backtest.created_at.desc())
        ).scalars().first()
        if bt:
            bn = add_node(
                NodeKind.EXPERIMENT.value, "回测", "backtest", bt.id,
                {"sharpe": (bt.metrics or {}).get("sharpe")},
            )
            add_edge(chain_tail, bn, "回测")
            chain_tail = bn

        val = db.execute(
            select(Validation).where(
                Validation.factor_id == f.id, Validation.status == ValidationStatus.SUCCESS.value
            ).order_by(Validation.created_at.desc())
        ).scalars().first()
        if val:
            grade = (val.robustness or {}).get("grade")
            vn = add_node(NodeKind.VALIDATION.value, f"科学验证 ({grade or '?'})", "validation", val.id,
                          {"grade": grade})
            add_edge(chain_tail, vn, "验证")
            chain_tail = vn
        last_terminal = chain_tail

    report = db.execute(
        select(ResearchReport).where(ResearchReport.project_id == project.id)
        .order_by(ResearchReport.created_at.desc())
    ).scalars().first()
    if report:
        rn = add_node(NodeKind.RESULT.value, f"研究报告: {report.grade or '—'}", "report", report.id,
                      {"grade": report.grade})
        add_edge(last_terminal, rn, "产出")

    db.commit()
    return {
        "project_id": str(project.id),
        "nodes": [
            {
                "id": str(n.id), "kind": n.kind, "label": n.label,
                "ref_type": n.ref_type, "ref_id": str(n.ref_id) if n.ref_id else None,
                "detail": n.detail, "order": n.order_index,
            }
            for n in nodes
        ],
        "edges": [
            {"from": str(e.from_node), "to": str(e.to_node), "label": e.label} for e in edges
        ],
    }

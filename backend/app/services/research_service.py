"""研究项目报告业务逻辑 (Sprint 8.1)。

聚合一个因子已有的研究产物 (最新成功回测 + 最新成功验证) → engine 生成叙事报告 → 落库。
报告是研究生态的核心资产 (后续研究员主页/社区基于它统计)。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine import ai_advisor, research_report
from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.market import DataSnapshot
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus


class FactorNotFoundError(Exception):
    pass


class NoResearchYetError(Exception):
    """因子还没有任何成功的回测或验证, 无法生成报告。"""


def _factor_brief(f: Factor) -> dict:
    return {
        "name": f.name,
        "kind": f.kind,
        "template_type": f.template_type,
        "spec": f.spec,
    }


def _latest_success_backtest(db: Session, owner_id: uuid.UUID, factor_id: uuid.UUID) -> Backtest | None:
    return db.execute(
        select(Backtest)
        .where(
            Backtest.owner_id == owner_id,
            Backtest.factor_id == factor_id,
            Backtest.status == BacktestStatus.SUCCESS.value,
        )
        .order_by(Backtest.created_at.desc())
    ).scalars().first()


def _latest_success_validation(db: Session, owner_id: uuid.UUID, factor_id: uuid.UUID) -> Validation | None:
    return db.execute(
        select(Validation)
        .where(
            Validation.owner_id == owner_id,
            Validation.factor_id == factor_id,
            Validation.status == ValidationStatus.SUCCESS.value,
        )
        .order_by(Validation.created_at.desc())
    ).scalars().first()


def _snapshot_brief(db: Session, snapshot_id: uuid.UUID | None) -> dict | None:
    if snapshot_id is None:
        return None
    snap = db.get(DataSnapshot, snapshot_id)
    if snap is None:
        return None
    return {
        "symbol": snap.symbol,
        "start_date": str(snap.start_date),
        "end_date": str(snap.end_date),
        "rows": snap.rows,
        "content_hash": snap.content_hash,
    }


def generate_for_factor(db: Session, owner: User, factor_id: uuid.UUID) -> ResearchReport:
    factor = db.get(Factor, factor_id)
    if factor is None or factor.owner_id != owner.id:
        raise FactorNotFoundError(str(factor_id))

    bt = _latest_success_backtest(db, owner.id, factor_id)
    val = _latest_success_validation(db, owner.id, factor_id)
    if bt is None and val is None:
        raise NoResearchYetError(str(factor_id))

    symbol = (val.symbol if val else None) or (bt.symbol if bt else "?")
    snapshot = _snapshot_brief(db, (bt.snapshot_id if bt else None) or (val.snapshot_id if val else None))

    validation_payload = None
    ai_suggestions = None
    if val:
        validation_payload = {
            "oos": val.oos,
            "walk_forward": val.walk_forward,
            "sensitivity": val.sensitivity,
            "robustness": val.robustness,
        }
        # 用本地确定性分析丰富"下一步建议"(无需 LLM)
        review = ai_advisor.local_validation_review(
            {"factor": _factor_brief(factor), "symbol": symbol, **validation_payload}
        )
        ai_suggestions = review.get("suggestions")

    sections = research_report.build_project_report(
        factor=_factor_brief(factor),
        symbol=symbol,
        backtest_metrics=bt.metrics if bt else None,
        validation=validation_payload,
        snapshot=snapshot,
        ai_suggestions=ai_suggestions,
    )

    report = ResearchReport(
        owner_id=owner.id,
        factor_id=factor_id,
        symbol=symbol,
        title=sections["title"],
        hypothesis=sections["hypothesis"],
        grade=sections.get("grade"),
        stages=sections["stages"],
        narrative=sections,
        based_on={
            "backtest_id": str(bt.id) if bt else None,
            "validation_id": str(val.id) if val else None,
        },
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: uuid.UUID) -> ResearchReport | None:
    return db.get(ResearchReport, report_id)


def list_my_reports(db: Session, owner_id: uuid.UUID, limit: int = 50) -> list[ResearchReport]:
    return list(
        db.execute(
            select(ResearchReport)
            .where(ResearchReport.owner_id == owner_id)
            .order_by(ResearchReport.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

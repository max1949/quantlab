"""项目级研究质量评估 (发布 / 分享闸门)。"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.validation import Validation, ValidationStatus
from engine.research_quality import QualityThresholds, QualityVerdict, assess_publish_readiness


class ResearchQualityError(Exception):
    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


def _thresholds() -> QualityThresholds:
    s = get_settings()
    if not s.research_gate_enabled:
        return QualityThresholds(
            min_oos_sharpe=-999.0,
            min_robustness_score=-999.0,
            min_backtest_sharpe=-999.0,
            require_sealed_holdout_positive=False,
            min_sealed_holdout_sharpe=-999.0,
        )
    return QualityThresholds(
        min_oos_sharpe=s.publish_min_oos_sharpe,
        min_robustness_score=s.publish_min_robustness_score,
        min_backtest_sharpe=s.publish_min_backtest_sharpe,
        require_sealed_holdout_positive=s.publish_require_sealed_holdout,
        min_sealed_holdout_sharpe=s.publish_min_sealed_holdout_sharpe,
    )


def _latest_success_backtest(db: Session, factor_id: uuid.UUID) -> Backtest | None:
    return db.execute(
        select(Backtest)
        .where(Backtest.factor_id == factor_id, Backtest.status == BacktestStatus.SUCCESS.value)
        .order_by(Backtest.created_at.desc())
    ).scalars().first()


def _latest_success_validation(db: Session, factor_id: uuid.UUID) -> Validation | None:
    return db.execute(
        select(Validation)
        .where(Validation.factor_id == factor_id, Validation.status == ValidationStatus.SUCCESS.value)
        .order_by(Validation.created_at.desc())
    ).scalars().first()


def assess_factor(db: Session, factor_id: uuid.UUID) -> QualityVerdict:
    bt = _latest_success_backtest(db, factor_id)
    val = _latest_success_validation(db, factor_id)
    return assess_publish_readiness(
        backtest_metrics=bt.metrics if bt else None,
        validation_status=val.status if val else None,
        validation_oos=val.oos if val else None,
        validation_robustness=val.robustness if val else None,
        thresholds=_thresholds(),
    )


def assess_project(db: Session, project_id: uuid.UUID) -> QualityVerdict:
    if not get_settings().research_gate_enabled:
        return QualityVerdict(passed=True, reasons=[], scorecard={})

    factors = list(
        db.execute(select(Factor.id).where(Factor.project_id == project_id)).scalars().all()
    )
    if not factors:
        return QualityVerdict(
            passed=False,
            reasons=["项目下还没有因子"],
            scorecard={},
        )
    # 以项目主因子 (最早创建的) 为准
    factor_id = factors[0]
    return assess_factor(db, factor_id)


def require_project_publishable(db: Session, project_id: uuid.UUID) -> QualityVerdict:
    verdict = assess_project(db, project_id)
    if not verdict.passed:
        raise ResearchQualityError(verdict.reasons)
    return verdict


def paper_nav_preview(db: Session, factor_id: uuid.UUID, owner_id: uuid.UUID, bars: int = 120) -> dict:
    """模拟跟踪预览: 用验证时封印段之后的逻辑, 在最近 bars 上滚动净值。"""
    from backend.app.services.paper_tracking_service import PaperTrackingError, compute_paper_nav

    try:
        return compute_paper_nav(db, factor_id, owner_id, bars=bars)
    except PaperTrackingError as exc:
        raise ResearchQualityError([exc.message])


def paper_preview_with_decay(db: Session, factor_id: uuid.UUID, owner_id: uuid.UUID, bars: int | None = None) -> dict:
    from backend.app.services import paper_tracking_service as pts

    try:
        preview = pts.compute_paper_nav(db, factor_id, owner_id, bars=bars)
    except pts.PaperTrackingError as exc:
        raise ResearchQualityError([exc.message])
    preview["decay"] = pts.assess_factor_decay(db, factor_id, owner_id, preview=preview)
    return preview

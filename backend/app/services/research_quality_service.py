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
    from backend.app.services import factor_service, market_data
    from engine.backtest import run_backtest
    from engine.cost_model import CostConfig

    factor = factor_service.get_factor(db, owner_id, factor_id)
    val = _latest_success_validation(db, factor_id)
    if val is None:
        raise ResearchQualityError(["需要先完成科学验证"])
    symbol = val.symbol
    ohlcv = market_data.load_ohlcv(symbol)
    tail = ohlcv.iloc[-bars:] if ohlcv.shape[0] > bars else ohlcv
    signal = factor_service._compute_series(db, owner_id, factor, tail)
    cfg = CostConfig(**(val.cost_config or {}))
    result = run_backtest(signal, tail, cfg)
    return {
        "factor_id": str(factor_id),
        "symbol": symbol,
        "bars": int(tail.shape[0]),
        "metrics": result.get("metrics") or {},
        "equity_curve": result.get("equity_curve") or [],
        "validation_grade": (val.robustness or {}).get("grade"),
        "note": "此为最近行情上的模拟跟踪预览, 非实盘承诺",
    }

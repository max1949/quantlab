"""项目级研究质量评估 (发布 / 分享闸门)。"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.project import ProjectStatus, ResearchProject
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus
from engine.research_quality import (
    PaperThresholds,
    QualityThresholds,
    QualityVerdict,
    assess_paper_readiness,
    assess_publish_readiness,
)


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
            max_turnover=None,
            min_abs_ic=None,
            allowed_robustness_grades=frozenset({"稳健", "中等", "偏弱", "脆弱"}),
        )
    grades = frozenset(
        g.strip() for g in s.publish_min_robustness_grades.split(",") if g.strip()
    ) or frozenset({"稳健", "中等"})
    return QualityThresholds(
        min_oos_sharpe=s.publish_min_oos_sharpe,
        min_robustness_score=s.publish_min_robustness_score,
        min_backtest_sharpe=s.publish_min_backtest_sharpe,
        require_sealed_holdout_positive=s.publish_require_sealed_holdout,
        min_sealed_holdout_sharpe=s.publish_min_sealed_holdout_sharpe,
        max_turnover=s.publish_max_turnover if s.publish_max_turnover > 0 else None,
        min_abs_ic=s.publish_min_abs_ic if s.publish_min_abs_ic > 0 else None,
        allowed_robustness_grades=grades,
    )


def _representative_factor_id(db: Session, project_id: uuid.UUID) -> uuid.UUID | None:
    from backend.app.models.factor import Factor

    factors = list(
        db.execute(select(Factor).where(Factor.project_id == project_id)).scalars().all()
    )
    if not factors:
        return None
    for f in factors:
        if _latest_success_validation(db, f.id):
            return f.id
    for f in factors:
        if _latest_success_backtest(db, f.id):
            return f.id
    return factors[0].id


def _paper_thresholds() -> PaperThresholds:
    s = get_settings()
    if not s.research_gate_enabled:
        return PaperThresholds(
            min_oos_sharpe=-999.0,
            min_robustness_score=-999.0,
            min_backtest_sharpe=-999.0,
            require_sealed_holdout_positive=False,
            min_sealed_holdout_sharpe=-999.0,
            max_turnover=None,
            min_abs_ic=None,
            min_regime_fit_score=-999,
            allowed_robustness_grades=frozenset({"稳健", "中等", "偏弱", "脆弱"}),
        )
    grades = frozenset(
        g.strip() for g in s.publish_min_robustness_grades.split(",") if g.strip()
    ) or frozenset({"稳健", "中等"})
    return PaperThresholds(
        min_oos_sharpe=max(s.publish_min_oos_sharpe, 0.25),
        min_robustness_score=max(s.publish_min_robustness_score, 55.0),
        min_backtest_sharpe=max(s.publish_min_backtest_sharpe, 0.1),
        require_sealed_holdout_positive=s.publish_require_sealed_holdout,
        min_sealed_holdout_sharpe=s.publish_min_sealed_holdout_sharpe,
        max_turnover=60.0 if s.publish_max_turnover <= 0 else min(s.publish_max_turnover, 60.0),
        min_abs_ic=s.publish_min_abs_ic if s.publish_min_abs_ic > 0 else 0.02,
        allowed_robustness_grades=grades,
        min_regime_fit_score=35,
    )


def paper_thresholds_payload() -> dict:
    th = _paper_thresholds()
    return {
        "min_oos_sharpe": th.min_oos_sharpe,
        "min_robustness_score": th.min_robustness_score,
        "min_backtest_sharpe": th.min_backtest_sharpe,
        "min_sealed_holdout_sharpe": th.min_sealed_holdout_sharpe,
        "max_turnover": th.max_turnover,
        "min_abs_ic": th.min_abs_ic,
        "min_regime_fit_score": th.min_regime_fit_score,
        "allowed_robustness_grades": sorted(th.allowed_robustness_grades),
    }


def assess_factor_paper(db: Session, factor_id: uuid.UUID, *, regime_fit_score: int | None = None) -> QualityVerdict:
    bt = _latest_success_backtest(db, factor_id)
    val = _latest_success_validation(db, factor_id)
    return assess_paper_readiness(
        backtest_metrics=bt.metrics if bt else None,
        validation_status=val.status if val else None,
        validation_oos=val.oos if val else None,
        validation_robustness=val.robustness if val else None,
        regime_fit_score=regime_fit_score,
        thresholds=_paper_thresholds(),
    )


def compute_mastery_stage(
    *,
    has_factor: bool,
    has_backtest: bool,
    has_validation: bool,
    publish_passed: bool,
    paper_passed: bool,
    is_published: bool,
) -> dict:
    """研究大师路径 — 告诉用户当前阶段与下一步。"""
    stages = [
        ("start", "start", 0),
        ("backtest", "backtest", 1),
        ("validate", "validation", 2),
        ("graduate", "graduate", 3),
        ("paper", "paper", 4),
        ("track", "track", 5),
        ("share", "publish", 6),
    ]
    if is_published:
        current = "share"
    elif paper_passed:
        current = "paper"
    elif publish_passed:
        current = "graduate"
    elif has_validation:
        current = "validate"
    elif has_backtest:
        current = "backtest"
    elif has_factor:
        current = "start"
    else:
        current = "start"

    next_map = {
        "start": "backtest",
        "backtest": "validate",
        "validate": "graduate",
        "graduate": "paper",
        "paper": "track",
        "track": "share",
        "share": "share",
    }
    idx = next(i for i, (k, _, _) in enumerate(stages) if k == current)
    return {
        "stage": current,
        "stage_index": idx,
        "total_stages": len(stages),
        "next_action": next_map[current],
        "progress_pct": round((idx + (1 if current == "share" else 0)) / len(stages) * 100),
    }


def thresholds_payload() -> dict:
    th = _thresholds()
    return {
        "min_oos_sharpe": th.min_oos_sharpe,
        "min_robustness_score": th.min_robustness_score,
        "min_backtest_sharpe": th.min_backtest_sharpe,
        "min_sealed_holdout_sharpe": th.min_sealed_holdout_sharpe,
        "max_turnover": th.max_turnover,
        "min_abs_ic": th.min_abs_ic,
        "allowed_robustness_grades": sorted(th.allowed_robustness_grades),
    }


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
    factor_id = _representative_factor_id(db, project_id)
    if factor_id is None:
        return QualityVerdict(passed=False, reasons=["项目下还没有因子"], scorecard={})
    return assess_factor(db, factor_id)


def orthogonal_preview(db: Session, project_id: uuid.UUID) -> dict | None:
    """发布前正交化预览 — 主因子相对同项目其它因子的冗余度 (非硬闸门)。"""
    from backend.app.models.project import ResearchProject
    from backend.app.models.user import User
    from backend.app.services import factor_service, market_data
    from engine import advanced_research as ar

    project = db.get(ResearchProject, project_id)
    if project is None or not project.symbol:
        return None
    factors = list(
        db.execute(select(Factor).where(Factor.project_id == project_id)).scalars().all()
    )
    if len(factors) < 2:
        return None
    rep_id = _representative_factor_id(db, project_id)
    if rep_id is None:
        return None
    target = next((f for f in factors if f.id == rep_id), None)
    if target is None:
        return None
    controls = [f for f in factors if f.id != rep_id][:5]
    owner = db.get(User, target.owner_id)
    if owner is None:
        return None
    if market_data.get_dataset(db, project.symbol) is None:
        return None
    ohlcv = market_data.load_ohlcv(project.symbol, "1d")
    try:
        target_signal = factor_service._compute_series(db, owner.id, target, ohlcv)
        control_signals = {
            f.name: factor_service._compute_series(db, owner.id, f, ohlcv)
            for f in controls
        }
        result = ar.orthogonalize(target_signal, control_signals)
    except ValueError:
        return None
    hint = None
    r2 = result.get("r2")
    if r2 is not None and float(r2) >= 0.5:
        names = "、".join(f.name for f in controls)
        hint = (
            f"主因子「{target.name}」与同项目因子（{names}）解释度 R²={float(r2):.2f}，"
            "发布前请确认是否仍有独立增量价值。"
        )
    return {
        "target_factor": target.name,
        "control_factors": [f.name for f in controls],
        "r2": r2,
        "unique_ratio": result.get("unique_ratio"),
        "verdict": result.get("verdict"),
        "hint": hint,
    }


def project_quality_payload(db: Session, project_id: uuid.UUID) -> dict:
    verdict = assess_project(db, project_id)
    hints: list[str] = []
    orth = orthogonal_preview(db, project_id)
    if orth and orth.get("hint"):
        hints.append(orth["hint"])

    project = db.get(ResearchProject, project_id)
    factor_id = _representative_factor_id(db, project_id)
    regime = None
    regime_fit_score = None
    if project and factor_id and project.owner_id:
        owner = db.get(User, project.owner_id)
        factor = db.get(Factor, factor_id)
        if owner and factor:
            from backend.app.services import regime_advisory

            regime = regime_advisory.market_regime_for_symbol(
                db, owner, project.symbol or "RB", "1d", factor=factor
            )
            if regime:
                regime_fit_score = regime.get("fit_score")

    paper_verdict = (
        assess_factor_paper(db, factor_id, regime_fit_score=regime_fit_score)
        if factor_id
        else QualityVerdict(passed=False, reasons=["项目下还没有因子"], scorecard={})
    )
    if paper_verdict.passed:
        hints.append("已通过模拟盘毕业线 — 可一键提交 Paper 订单并开启真实跟踪。")
    elif paper_verdict.reasons and verdict.passed:
        hints.append("发布线已通过，但模拟盘毕业线更严 — 请按下方 Paper 清单继续优化。")

    factors = list(
        db.execute(select(Factor.id).where(Factor.project_id == project_id)).scalars().all()
    )
    has_factor = bool(factors)
    has_backtest = factor_id is not None and _latest_success_backtest(db, factor_id) is not None
    has_validation = factor_id is not None and _latest_success_validation(db, factor_id) is not None
    is_published = project is not None and project.status == ProjectStatus.PUBLISHED.value

    mastery = compute_mastery_stage(
        has_factor=has_factor,
        has_backtest=has_backtest,
        has_validation=has_validation,
        publish_passed=verdict.passed,
        paper_passed=paper_verdict.passed,
        is_published=is_published,
    )

    return {
        "passed": verdict.passed,
        "reasons": verdict.reasons,
        "scorecard": verdict.scorecard,
        "thresholds": thresholds_payload(),
        "paper_ready": paper_verdict.passed,
        "paper_reasons": paper_verdict.reasons,
        "paper_scorecard": paper_verdict.scorecard,
        "paper_thresholds": paper_thresholds_payload(),
        "factor_id": str(factor_id) if factor_id else None,
        "symbol": project.symbol if project else None,
        "regime": regime,
        "mastery": mastery,
        "hints": hints,
        "orthogonal": orth,
    }


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

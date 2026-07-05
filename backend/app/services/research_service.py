"""研究项目报告业务逻辑 (Sprint 8.1)。

聚合一个因子已有的研究产物 (最新成功回测 + 最新成功验证) → engine 生成叙事报告 → 落库。
报告是研究生态的核心资产 (后续研究员主页/社区基于它统计)。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine import ai_advisor, research_report
from backend.app.schemas.research import ReportSummary
from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.market import DataSnapshot
from backend.app.models.project import ProjectStatus, ResearchProject
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus


class FactorNotFoundError(Exception):
    pass


class ProjectNotFoundError(Exception):
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


def _build_report_row(
    db: Session, owner: User, factor: Factor, project_id: uuid.UUID | None
) -> ResearchReport:
    factor_id = factor.id
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

    result_text = "\n".join(sections.get("result_summary") or []) or "尚无回测/验证结果。"
    summary = (sections.get("result_summary") or [sections["title"]])[0]
    report = ResearchReport(
        owner_id=owner.id,
        project_id=project_id,
        factor_id=factor_id,
        factor_version=factor.version,
        symbol=symbol,
        title=sections["title"],
        summary=summary,
        hypothesis=sections["hypothesis"],
        methodology=sections["experiment"],
        result=result_text,
        risk_analysis="\n".join(sections.get("risks") or []),
        improvement_suggestion="\n".join(sections.get("next_steps") or []),
        grade=sections.get("grade"),
        stages=sections["stages"],
        narrative=sections,
        based_on={
            "backtest_id": str(bt.id) if bt else None,
            "validation_id": str(val.id) if val else None,
        },
        is_public=False,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Growth OS 钩子: 报告=完成一次研究 -> 刷新研究信用、激活邀请、埋点。
    from backend.app.services import growth_service, referral_service

    growth_service.recompute_contribution_score(db, owner)
    referral_service.activate_if_referred(db, owner)
    growth_service.log_event(db, "generate_report", owner.id, {"report_id": str(report.id)})
    from backend.app.services import academy_hooks

    report.academy_rewards = academy_hooks.on_report_generated(db, owner)
    return report


def generate_for_factor(db: Session, owner: User, factor_id: uuid.UUID) -> ResearchReport:
    factor = db.get(Factor, factor_id)
    if factor is None or factor.owner_id != owner.id:
        raise FactorNotFoundError(str(factor_id))
    return _build_report_row(db, owner, factor, factor.project_id)


def _representative_factor(db: Session, owner_id: uuid.UUID, project_id: uuid.UUID) -> Factor | None:
    """项目代表性因子: 优先有成功验证的, 其次有成功回测的, 再次任意。"""
    factors = list(
        db.execute(select(Factor).where(Factor.project_id == project_id)).scalars().all()
    )
    if not factors:
        return None
    for f in factors:
        if _latest_success_validation(db, owner_id, f.id):
            return f
    for f in factors:
        if _latest_success_backtest(db, owner_id, f.id):
            return f
    return factors[0]


def generate_for_project(db: Session, owner: User, project_id: uuid.UUID) -> ResearchReport:
    from backend.app.models.project import ResearchProject

    proj = db.get(ResearchProject, project_id)
    if proj is None or proj.owner_id != owner.id:
        raise ProjectNotFoundError(str(project_id))
    factor = _representative_factor(db, owner.id, project_id)
    if factor is None:
        raise NoResearchYetError(str(project_id))
    return _build_report_row(db, owner, factor, project_id)


def get_report(db: Session, report_id: uuid.UUID) -> ResearchReport | None:
    return db.get(ResearchReport, report_id)


def public_report_ids(db: Session, limit: int = 500) -> list[tuple[uuid.UUID, datetime]]:
    """公开且已发布的报告 (id, 更新/创建时间), 供 sitemap 使用。"""
    rows = db.execute(
        select(ResearchReport.id, ResearchReport.created_at)
        .join(ResearchProject, ResearchProject.id == ResearchReport.project_id)
        .where(
            ResearchReport.is_public.is_(True),
            ResearchProject.status == ProjectStatus.PUBLISHED.value,
        )
        .order_by(ResearchReport.created_at.desc())
        .limit(max(1, min(int(limit), 2000)))
    ).all()
    return [(r[0], r[1]) for r in rows]


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


_GRADE_RANK = {"稳健": 3, "中等": 2, "偏弱": 1, "脆弱": 0}


def _validation_metrics(val: Validation | None) -> tuple[float | None, float | None]:
    if val is None:
        return None, None
    oos_sharpe = None
    if val.oos:
        s = (val.oos.get("out_of_sample") or {}).get("sharpe")
        oos_sharpe = float(s) if s is not None else None
    rob_score = None
    if val.robustness and val.robustness.get("score") is not None:
        rob_score = float(val.robustness["score"])
    return oos_sharpe, rob_score


def _feed_metrics(db: Session, report: ResearchReport) -> tuple[float | None, float | None]:
    vid = (report.based_on or {}).get("validation_id")
    if not vid:
        return None, None
    try:
        val = db.get(Validation, uuid.UUID(str(vid)))
    except (ValueError, TypeError):
        return None, None
    return _validation_metrics(val)


def _feed_factor_meta(db: Session, report: ResearchReport) -> dict:
    factor = db.get(Factor, report.factor_id)
    timeframe = "1d"
    for key in ("validation_id", "backtest_id"):
        raw = (report.based_on or {}).get(key)
        if not raw:
            continue
        try:
            ref_id = uuid.UUID(str(raw))
        except (TypeError, ValueError):
            continue
        model = Validation if key == "validation_id" else Backtest
        row = db.get(model, ref_id)
        if row and row.snapshot_id:
            snap = db.get(DataSnapshot, row.snapshot_id)
            if snap and snap.timeframe:
                timeframe = snap.timeframe
                break
    return {
        "factor_kind": factor.kind if factor else None,
        "factor_template": factor.template_type if factor else None,
        "timeframe": timeframe,
    }


def _feed_mastery_badges(db: Session, report: ResearchReport) -> dict:
    """大师化徽章 — Paper 毕业线 / 模拟跟踪 (Feed 卡片展示)。"""
    out = {
        "paper_graduated": False,
        "paper_tracking": False,
        "mastery_badge": None,
    }
    if not report.factor_id:
        return out

    from backend.app.models.execution import PaperOrder
    from backend.app.services import research_quality_service as rqs

    factor = db.get(Factor, report.factor_id)
    project = db.get(ResearchProject, report.project_id) if report.project_id else None
    regime_fit_score = None
    if factor and project and report.owner_id:
        owner = db.get(User, report.owner_id)
        if owner:
            from backend.app.services import regime_advisory

            regime = regime_advisory.market_regime_for_symbol(
                db,
                owner,
                project.symbol or report.symbol or "RB",
                "1d",
                factor=factor,
            )
            if regime:
                regime_fit_score = regime.get("fit_score")

    verdict = rqs.assess_factor_paper(
        db, report.factor_id, regime_fit_score=regime_fit_score
    )
    has_po = (
        db.execute(
            select(PaperOrder.id).where(PaperOrder.factor_id == report.factor_id).limit(1)
        ).first()
        is not None
    )
    out["paper_graduated"] = verdict.passed
    out["paper_tracking"] = has_po
    if verdict.passed and has_po:
        out["mastery_badge"] = "track"
    elif verdict.passed:
        out["mastery_badge"] = "paper"
    return out


def feed_summary(
    db: Session,
    report: ResearchReport,
    metric: tuple[float | None, float | None] | None = None,
    badges: dict | None = None,
    *,
    mastery_path: dict | None = None,
) -> dict:
    oos_sharpe, robustness_score = metric or _feed_metrics(db, report)
    mastery = badges if badges is not None else _feed_mastery_badges(db, report)
    out = {
        **ReportSummary.model_validate(report).model_dump(),
        "oos_sharpe": oos_sharpe,
        "robustness_score": robustness_score,
        **_feed_factor_meta(db, report),
        **mastery,
    }
    if mastery_path is not None:
        out["mastery_path"] = mastery_path
    return out


def feed(db: Session, sort: str = "latest", limit: int = 30, *, graduated_only: bool = False) -> list[dict]:
    """研究 Feed: 公开报告。sort=latest(最新) | top(高评分优先)。"""
    limit = max(1, min(int(limit), 50))
    rows = list(
        db.execute(
            select(ResearchReport)
            .join(ResearchProject, ResearchProject.id == ResearchReport.project_id)
            .where(
                ResearchReport.is_public.is_(True),
                ResearchProject.status == ProjectStatus.PUBLISHED.value,
            )
            .order_by(ResearchReport.created_at.desc())
            .limit(200)
        ).scalars().all()
    )
    validation_ids: list[uuid.UUID] = []
    for row in rows:
        raw = (row.based_on or {}).get("validation_id")
        if not raw:
            continue
        try:
            validation_ids.append(uuid.UUID(str(raw)))
        except (TypeError, ValueError):
            continue
    validations = {
        v.id: v
        for v in db.execute(select(Validation).where(Validation.id.in_(validation_ids))).scalars().all()
    } if validation_ids else {}
    metrics_by_report: dict[uuid.UUID, tuple[float | None, float | None]] = {}
    for row in rows:
        raw = (row.based_on or {}).get("validation_id")
        try:
            val_id = uuid.UUID(str(raw)) if raw else None
        except (TypeError, ValueError):
            val_id = None
        metrics_by_report[row.id] = _validation_metrics(validations.get(val_id)) if val_id else (None, None)
    badges_by_report = {r.id: _feed_mastery_badges(db, r) for r in rows}
    if graduated_only:
        rows = [r for r in rows if badges_by_report.get(r.id, {}).get("paper_graduated")]
    if sort == "top":
        rows.sort(
            key=lambda r: (
                badges_by_report.get(r.id, {}).get("paper_graduated", False),
                _GRADE_RANK.get(r.grade or "", -1),
                metrics_by_report.get(r.id, (None, None))[1] or 0,
                metrics_by_report.get(r.id, (None, None))[0] or 0,
                r.created_at,
            ),
            reverse=True,
        )
    from backend.app.services import onboarding_service

    path_by_owner: dict[uuid.UUID, dict] = {}
    out_rows = []
    for r in rows[:limit]:
        mp = None
        if r.owner_id:
            if r.owner_id not in path_by_owner:
                owner = db.get(User, r.owner_id)
                if owner:
                    path_by_owner[r.owner_id] = onboarding_service.mastery_path_snapshot_for_user(
                        db, owner, "en"
                    )
            mp = path_by_owner.get(r.owner_id)
        out_rows.append(
            feed_summary(db, r, metrics_by_report.get(r.id), badges_by_report.get(r.id), mastery_path=mp)
        )
    return out_rows

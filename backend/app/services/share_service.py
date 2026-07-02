"""研究分享卡片 (Sprint 9A)。

把一份研究报告生成可公开转发的卡片 (/share/{token}), 免登录可看 ->
每一次研究都能变成传播素材, 驱动获取闭环。
"""

from __future__ import annotations

import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.growth import ResearchShare
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.services import growth_service

SHARE_REWARD = 5  # 首次为某报告生成分享卡片, 给 reward_points


class ReportNotFoundError(Exception):
    pass


class ShareNotFoundError(Exception):
    pass


def _build_card(report: ResearchReport, owner: User) -> dict:
    return {
        "title": report.title,
        "researcher": owner.username,
        "researcher_level": owner.level,
        "symbol": report.symbol,
        "grade": report.grade,
        "summary": report.summary,
        "hypothesis": report.hypothesis,
    }


def create_share(db: Session, owner: User, report_id: uuid.UUID) -> ResearchShare:
    from backend.app.services import research_quality_service as rq
    from backend.app.services.research_quality_service import ResearchQualityError

    report = db.get(ResearchReport, report_id)
    if report is None or report.owner_id != owner.id:
        raise ReportNotFoundError(str(report_id))

    if report.project_id:
        try:
            rq.require_project_publishable(db, report.project_id)
        except ResearchQualityError as exc:
            raise ReportNotFoundError("; ".join(exc.reasons)) from exc

    existing = db.execute(
        select(ResearchShare).where(ResearchShare.report_id == report_id)
    ).scalar_one_or_none()
    if existing is not None:
        # 复用已存在的分享 (刷新卡片快照)。
        existing.card = _build_card(report, owner)
        db.commit()
        db.refresh(existing)
        existing.academy_rewards = []
        return existing

    share = ResearchShare(
        report_id=report_id,
        owner_id=owner.id,
        token=secrets.token_urlsafe(12)[:24],
        card=_build_card(report, owner),
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    # 报告默认公开 (可被分享页看到)。
    if not report.is_public:
        report.is_public = True
        db.commit()
    growth_service.award_reward_points(db, owner, SHARE_REWARD)
    growth_service.log_event(db, "share", owner.id, {"report_id": str(report_id), "token": share.token})
    from backend.app.services import academy_hooks

    share.academy_rewards = academy_hooks.on_first_share(db, owner)
    return share


def get_share(db: Session, token: str, *, count_view: bool = True) -> ResearchShare:
    share = db.execute(
        select(ResearchShare).where(ResearchShare.token == token)
    ).scalar_one_or_none()
    if share is None:
        raise ShareNotFoundError(token)
    if count_view:
        share.views = (share.views or 0) + 1
        db.commit()
        db.refresh(share)
    return share

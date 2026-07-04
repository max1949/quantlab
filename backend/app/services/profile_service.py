"""研究员主页 (Sprint 8): 类似 GitHub Profile 的研究档案与统计。

聚合用户的研究行为数据 (项目/因子/有效验证/报告/积分/研究方向标签), 把"研究行为"
变成可展示的长期身份资产 —— 这是研究生态比模拟盘更值钱的地方。
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.locale import Locale
from backend.app.i18n.content import factor_template_label, level_label
from backend.app.models.factor import Factor
from backend.app.models.project import ResearchProject
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus


def _count(db: Session, stmt) -> int:
    return int(db.execute(stmt).scalar_one() or 0)


def build_profile(
    db: Session, user: User, viewer: User | None = None, locale: Locale = "en"
) -> dict:
    uid = user.id

    project_count = _count(
        db, select(func.count(ResearchProject.id)).where(ResearchProject.owner_id == uid)
    )
    factor_count = _count(db, select(func.count(Factor.id)).where(Factor.owner_id == uid))
    report_count = _count(
        db, select(func.count(ResearchReport.id)).where(ResearchReport.owner_id == uid)
    )

    # 有效验证: 成功且稳健性达"中等"以上。
    success_vals = list(
        db.execute(
            select(Validation.robustness).where(
                Validation.owner_id == uid,
                Validation.status == ValidationStatus.SUCCESS.value,
            )
        ).scalars().all()
    )
    validation_count = len(success_vals)
    effective_validation_count = sum(
        1 for rob in success_vals if (rob or {}).get("grade") in {"稳健", "中等"}
    )

    # 研究方向标签: 由因子模板类型聚合。
    tt_rows = db.execute(
        select(Factor.template_type, func.count(Factor.id))
        .where(Factor.owner_id == uid, Factor.template_type.is_not(None))
        .group_by(Factor.template_type)
        .order_by(func.count(Factor.id).desc())
    ).all()
    tags = [factor_template_label(tt, locale) for tt, _ in tt_rows if tt]

    from backend.app.services import social_service

    follow_counts = social_service.counts(db, uid)
    from backend.app.services import research_quality_service as rqs

    mastery_counts = rqs.user_paper_mastery_counts(db, uid)
    out = {
        "user_id": str(uid),
        "username": user.username,
        "level": user.level,
        "level_label": level_label(locale, user.level),
        "research_score": round(user.research_score or 0.0, 2),
        "reward_points": user.reward_points or 0,
        "research_contribution_score": round(user.research_contribution_score or 0.0, 2),
        "experience": user.experience,
        "project_count": project_count,
        "factor_count": factor_count,
        "validation_count": validation_count,
        "effective_validation_count": effective_validation_count,
        "report_count": report_count,
        "paper_graduated_count": mastery_counts["paper_graduated_count"],
        "paper_tracking_count": mastery_counts["paper_tracking_count"],
        "followers": follow_counts["followers"],
        "following": follow_counts["following"],
        "is_following": False,
        "tags": tags,
        "joined_at": user.created_at,
    }
    if viewer is not None and viewer.id != uid:
        out["is_following"] = social_service.is_following(db, viewer.id, uid)
    return out


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)

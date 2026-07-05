"""新手一页纸手册 PDF — 快速上手 + 大师路径 + 下一步指引。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.user import User
from backend.app.services import onboarding_service


def beginner_onepager_lines(db: Session, user: User, locale: Locale) -> list[str]:
    flags = onboarding_service._journey_flags(db, user)
    mastery_goal = onboarding_service._mastery_goal_payload(db, user, locale)
    active_id = onboarding_service._active_project_id(db, user)
    path = onboarding_service.mastery_path_snapshot_for_user(
        db,
        user,
        locale,
        flags=flags,
        mastery_goal=mastery_goal,
        active_project_id=active_id,
    )
    nxt = onboarding_service.next_step(db, user, locale)
    labels = i18n.BEGINNER_ONEPAGER.get(locale) or i18n.BEGINNER_ONEPAGER["en"]
    qs = i18n.QUICKSTART_GUIDE.get(locale) or i18n.QUICKSTART_GUIDE["en"]
    ov = i18n.MASTERY_OVERVIEW.get(locale) or i18n.MASTERY_OVERVIEW["en"]

    lines = [
        labels["doc_title"],
        labels["user_line"].format(username=user.username),
        labels["progress_line"].format(done=path["done_count"], total=path["total"]),
        "---",
        labels["section_quickstart"],
        labels["step_line"].format(n=1, label=qs["step1_label"]),
        f"  {qs['step1_hint']}",
        labels["step_line"].format(n=2, label=qs["step2_label"]),
        f"  {qs['step2_hint']}",
        labels["step_line"].format(n=3, label=qs["step3_label"]),
        f"  {qs['step3_hint']}",
        "---",
        labels["section_mastery"],
    ]
    for phase in path["phases"]:
        mark = labels["done_mark"] if phase["done"] else labels["todo_mark"]
        hint_key = f"phase_{phase['key']}_hint"
        hint = ov.get(hint_key, "")
        lines.append(f"{mark} {phase['label']}")
        if hint:
            lines.append(f"    {hint}")
    lines.extend(
        [
            "---",
            labels["section_next"],
            str(nxt.get("action") or nxt.get("stage") or ""),
            "---",
            labels["section_sprint"],
            labels["sprint_hint"],
            "---",
            labels["footer"],
        ]
    )
    return lines


def render_beginner_onepager_pdf(db: Session, user: User, locale: Locale) -> bytes:
    from backend.app.services.billing_ledger_service import _pdf_text_lines

    return _pdf_text_lines(beginner_onepager_lines(db, user, locale))

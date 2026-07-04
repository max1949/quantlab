"""Pro 升级教练与 Stripe 回跳测试。"""

from __future__ import annotations

from backend.app.models.user import User, UserLevel
from backend.app.services import membership_service as ms


def test_upgrade_coaching_when_paper_ready(db_session):
    user = User(
        email="up@x.com",
        username="upuser",
        hashed_password="x",
        level=UserLevel.L4,
    )
    db_session.add(user)
    db_session.commit()

    out = ms.upgrade_coaching_payload(
        db_session,
        user,
        "zh",
        mastery_goal={"paper_ready": True, "mastery_next_action": "paper"},
        challenge_paper_coaching=None,
    )
    assert out is not None
    assert out["plan_code"] == "pro_monthly"
    assert out["reason"] == "paper_ready"
    assert "Paper" in out["message"] or "专业" in out["message"]


def test_upgrade_coaching_hidden_when_pro(db_session):
    user = User(
        email="pro@x.com",
        username="prouser",
        hashed_password="x",
        level=UserLevel.L4,
    )
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    out = ms.upgrade_coaching_payload(
        db_session,
        user,
        "en",
        mastery_goal={"paper_ready": True},
        challenge_paper_coaching=None,
    )
    assert out is None


def test_frontend_origin_prefers_frontend_base_url(monkeypatch):
    from backend.app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "frontend_base_url", "https://web.quantlab.ai")
    monkeypatch.setattr(settings, "public_base_url", "https://api.quantlab.ai")
    assert ms.frontend_origin() == "https://web.quantlab.ai"

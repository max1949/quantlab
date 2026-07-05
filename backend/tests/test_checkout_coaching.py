"""支付成功解锁教练测试。"""

from __future__ import annotations

from backend.app.models.user import User, UserLevel
from backend.app.services import membership_service as ms


def test_post_checkout_coaching_plus(db_session):
    user = User(email="pc@x.com", username="pcuser", hashed_password="x", level=UserLevel.L2)
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PLUS, 30, "plus_monthly")

    out = ms.post_checkout_coaching_payload(
        db_session,
        user,
        "zh",
        "plus_monthly",
        mastery_goal={"mastery_next_action": "validation"},
        active_project_id=None,
        done_count=3,
    )
    assert out is not None
    assert out["plan_code"] == "plus_monthly"
    assert out["reason"] == "plus_validate"
    assert out["cta_action"] == "run_validation"
    assert out["unlock_features"]


def test_post_checkout_coaching_pro_paper_ready(db_session):
    user = User(email="pc2@x.com", username="pcuser2", hashed_password="x", level=UserLevel.L4)
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    out = ms.post_checkout_coaching_payload(
        db_session,
        user,
        "en",
        "pro_monthly",
        mastery_goal={"paper_ready": True, "mastery_next_action": "paper"},
        active_project_id=None,
        done_count=5,
    )
    assert out is not None
    assert out["reason"] == "pro_paper_ready"
    assert out["cta_action"] == "run_paper"


def test_post_checkout_coaching_hidden_when_tier_mismatch(db_session):
    user = User(email="pc3@x.com", username="pcuser3", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    out = ms.post_checkout_coaching_payload(
        db_session,
        user,
        "zh",
        "plus_monthly",
        mastery_goal={},
        active_project_id=None,
    )
    assert out is None

"""行情数据升级教练测试。"""

from __future__ import annotations

from backend.app.models.user import User
from backend.app.services import market_data_policy as mdp
from backend.app.services.market_data import seed_sample_market_data


def test_market_data_coaching_when_history_capped(db_session):
    seed_sample_market_data(db_session)
    user = User(email="md@x.com", username="mduser", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    out = mdp.market_data_coaching_payload(
        db_session,
        user,
        "zh",
        symbol="RB",
        has_active_research=True,
    )
    assert out is not None
    assert out["reason"] in ("free_history_cap", "free_upgrade_hint")
    assert out["effective_rows"] is not None
    assert out["plan_code"] in ("plus_monthly", "pro_monthly")
    assert "stripe_available" in out


def test_market_data_coaching_hidden_without_research(db_session):
    seed_sample_market_data(db_session)
    user = User(email="md2@x.com", username="mduser2", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    out = mdp.market_data_coaching_payload(
        db_session,
        user,
        "en",
        symbol="RB",
        has_active_research=False,
    )
    assert out is None

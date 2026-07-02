"""Python 因子快评 API 测试。"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data
from backend.tests.test_growth import BASE, _register
from backend.tests.test_python_factor import GOOD

def test_python_evaluate_requires_entitlement(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "pe0")
    r = client.post(
        f"{BASE}/factors/python/evaluate",
        headers=h,
        json={"source": GOOD, "symbol": "RB", "timeframe": "1d"},
    )
    assert r.status_code == 403


def test_python_evaluate_with_l3_plus(client, db_session):
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    h = _register(client, "pe1")
    user = db_session.execute(select(User).where(User.username == "pe1")).scalar_one()
    user.level = UserLevel.L3
    db_session.commit()

    from backend.app.services import membership_service as ms

    ms.grant(db_session, user, tier=1, period_days=30, plan_code="plus_monthly", source="test")

    r = client.post(
        f"{BASE}/factors/python/evaluate",
        headers=h,
        json={"source": GOOD, "symbol": "RB", "timeframe": "1d"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "coach_summary" in body
    assert "publish_hints" in body
    assert "Python" in body["coach_summary"]


def test_python_evaluate_bad_source_422(client, db_session):
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    h = _register(client, "pe2")
    user = db_session.execute(select(User).where(User.username == "pe2")).scalar_one()
    user.level = UserLevel.L3
    db_session.commit()
    from backend.app.services import membership_service as ms

    ms.grant(db_session, user, tier=1, period_days=30, plan_code="plus_monthly", source="test")

    r = client.post(
        f"{BASE}/factors/python/evaluate",
        headers=h,
        json={"source": "eval('1')", "symbol": "RB"},
    )
    assert r.status_code == 422

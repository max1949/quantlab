"""公式因子快评 API 测试。"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data
from backend.tests.test_growth import BASE, _register


def test_formula_evaluate_requires_entitlement(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "fe0")
    r = client.post(
        f"{BASE}/factors/formula/evaluate",
        headers=h,
        json={"expr": "mom(close, 20)", "symbol": "RB", "timeframe": "1d"},
    )
    assert r.status_code == 403


def test_formula_evaluate_with_l2_plus(client, db_session):
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    h = _register(client, "fe1")
    user = db_session.execute(select(User).where(User.username == "fe1")).scalar_one()
    user.level = UserLevel.L2
    db_session.commit()

    from backend.app.services import membership_service as ms

    ms.grant(db_session, user, tier=1, period_days=30, plan_code="plus_monthly", source="test")

    r = client.post(
        f"{BASE}/factors/formula/evaluate",
        headers=h,
        json={"expr": "mom(close, 20)", "symbol": "RB", "timeframe": "1d"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["expr"] == "mom(close, 20)"
    assert "coach_summary" in body
    assert "publish_hints" in body


def test_formula_evaluate_bad_expr_422(client, db_session):
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    h = _register(client, "fe2")
    user = db_session.execute(select(User).where(User.username == "fe2")).scalar_one()
    user.level = UserLevel.L2
    db_session.commit()
    from backend.app.services import membership_service as ms

    ms.grant(db_session, user, tier=1, period_days=30, plan_code="plus_monthly", source="test")

    r = client.post(
        f"{BASE}/factors/formula/evaluate",
        headers=h,
        json={"expr": "__import__('os')", "symbol": "RB"},
    )
    assert r.status_code == 422

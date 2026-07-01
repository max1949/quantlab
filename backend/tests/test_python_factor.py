"""Python 因子 API 测试。"""

from __future__ import annotations

from backend.tests.test_growth import BASE, _register

GOOD = """
def compute(ohlcv):
    close = ohlcv["close"]
    return close.pct_change(5)
"""


def test_python_factor_requires_entitlement(client, db_session):
    h = _register(client, "py0")
    r = client.post(
        f"{BASE}/factors/python",
        headers=h,
        json={"name": "py", "source": GOOD},
    )
    assert r.status_code == 403


def test_python_factor_create_with_l3_plus(client, db_session):
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    h = _register(client, "py1")
    user = db_session.execute(select(User).where(User.username == "py1")).scalar_one()
    user.level = UserLevel.L3
    db_session.commit()

    from backend.app.services import membership_service as ms

    ms.grant(db_session, user, tier=1, period_days=30, plan_code="plus_monthly", source="test")

    r = client.post(
        f"{BASE}/factors/python",
        headers=h,
        json={"name": "my-py", "source": GOOD},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["kind"] == "python"
    prev = client.post(f"{BASE}/factors/{body['id']}/preview", headers=h)
    assert prev.status_code == 200

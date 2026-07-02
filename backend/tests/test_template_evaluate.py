"""模板因子快评 API 测试。"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data
from backend.tests.test_growth import BASE, _register


def test_template_evaluate_l0(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "te0")
    r = client.post(
        f"{BASE}/factors/template/evaluate",
        headers=h,
        json={
            "template_type": "momentum",
            "params": {"window": 20},
            "symbol": "RB",
            "timeframe": "1d",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["template_type"] == "momentum"
    assert body["params"]["window"] == 20
    assert "coach_summary" in body
    assert "模板参数" in body["coach_summary"]


def test_template_evaluate_bad_param_422(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "te1")
    r = client.post(
        f"{BASE}/factors/template/evaluate",
        headers=h,
        json={"template_type": "momentum", "params": {"window": 0}, "symbol": "RB"},
    )
    assert r.status_code == 422

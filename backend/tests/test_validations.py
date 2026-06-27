"""科学验证接口测试 (eager 模式)。

覆盖: 创建→成功、OOS/WF/敏感性/稳健性齐全、组合器敏感性退化、错误分支、鉴权。
"""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.user import User
from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"
USER = {"email": "val@quantlab.ai", "username": "valtester", "password": "s3cret-pass"}


def _auth(client) -> dict:
    client.post(f"{BASE}/auth/register", json=USER)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _template(client, h, name="mom") -> str:
    return client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": name, "template_type": "momentum", "params": {"window": 20}},
    ).json()["id"]


def test_validation_runs_full(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = _template(client, h)
    resp = client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "success"
    assert body["snapshot_id"]
    # 三类验证 + 稳健性
    assert set(body["oos"]) >= {"in_sample", "out_of_sample", "sharpe_degradation"}
    assert len(body["walk_forward"]["folds"]) == 4
    assert body["sensitivity"]["summary"]["n_variants"] >= 2  # 模板因子扫窗口
    rob = body["robustness"]
    assert 0 <= rob["score"] <= 100
    assert rob["grade"] in {"稳健", "中等", "偏弱", "脆弱"}


def test_validation_stack_sensitivity_degrades(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    f1 = _template(client, h, "c1")
    f2 = _template(client, h, "c2")
    # 升 L1 建组合器
    user = db_session.execute(
        select(User).where(User.username == USER["username"])
    ).scalar_one()
    user.level = 1
    db_session.commit()
    sid = client.post(
        f"{BASE}/factors/stack",
        headers=h,
        json={"name": "stk", "components": [
            {"factor_id": f1, "weight": 0.5}, {"factor_id": f2, "weight": 0.5}]},
    ).json()["id"]

    body = client.post(
        f"{BASE}/validations", headers=h, json={"factor_id": sid, "symbol": "AU"}
    ).json()
    assert body["status"] == "success"
    # 组合器无单参可扫 -> 敏感性单点
    assert body["sensitivity"]["summary"]["n_variants"] == 1


def test_validation_unknown_factor_404(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fake = "00000000-0000-0000-0000-000000000000"
    assert client.post(
        f"{BASE}/validations", headers=h, json={"factor_id": fake, "symbol": "RB"}
    ).status_code == 404


def test_validation_unknown_symbol_404(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = _template(client, h)
    assert client.post(
        f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": "ZZZ"}
    ).status_code == 404


def test_list_and_get_validation(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = _template(client, h)
    vid = client.post(
        f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": "IF"}
    ).json()["id"]
    assert len(client.get(f"{BASE}/validations", headers=h).json()) == 1
    detail = client.get(f"{BASE}/validations/{vid}", headers=h)
    assert detail.status_code == 200
    assert detail.json()["symbol"] == "IF"


def test_validations_require_auth(client):
    assert client.get(f"{BASE}/validations").status_code == 403

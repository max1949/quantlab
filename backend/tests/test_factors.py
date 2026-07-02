"""因子实验室接口测试: 模板目录 / 模板因子 / 组合器等级闸门 / 预览 / 校验。"""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.user import User

BASE = "/api/v1"

USER = {
    "email": "quant@quantlab.ai",
    "username": "quant",
    "password": "s3cret-pass",
}


def _auth_headers(client) -> dict:
    client.post(f"{BASE}/auth/register", json=USER)
    token = client.post(
        f"{BASE}/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _set_level(db_session, level: int) -> None:
    user = db_session.execute(
        select(User).where(User.username == USER["username"])
    ).scalar_one()
    user.level = level
    db_session.commit()


def test_list_templates(client):
    h = _auth_headers(client)
    resp = client.get(f"{BASE}/factors/templates", headers=h)
    assert resp.status_code == 200
    codes = {t["code"] for t in resp.json()}
    assert {"momentum", "rsi", "volatility", "mean_reversion", "sma_ratio"} <= codes
    mom = next(t for t in resp.json() if t["code"] == "momentum")
    assert mom.get("how_it_works")
    win = next(p for p in mom["params"] if p["name"] == "window")
    assert win.get("help") and win["help"].get("tip")


def test_create_template_factor_l0(client):
    h = _auth_headers(client)
    resp = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "我的动量", "template_type": "momentum", "params": {"window": 30}},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["kind"] == "template"
    assert body["spec"]["params"]["window"] == 30


def test_create_template_bad_param_422(client):
    h = _auth_headers(client)
    resp = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "坏参数", "template_type": "momentum", "params": {"window": 0}},
    )
    assert resp.status_code == 422


def test_duplicate_name_409(client):
    h = _auth_headers(client)
    body = {"name": "dup", "template_type": "momentum", "params": {}}
    assert client.post(f"{BASE}/factors/template", headers=h, json=body).status_code == 201
    assert client.post(f"{BASE}/factors/template", headers=h, json=body).status_code == 409


def test_stack_blocked_for_l0(client):
    h = _auth_headers(client)
    # 先建一个模板因子作为组件
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "comp", "template_type": "momentum", "params": {}},
    ).json()["id"]
    # L0 用户创建组合器 -> 403 (require_level L1)
    resp = client.post(
        f"{BASE}/factors/stack",
        headers=h,
        json={"name": "组合", "components": [{"factor_id": fid, "weight": 1.0}]},
    )
    assert resp.status_code == 403


def test_stack_allowed_for_l1_and_preview(client, db_session):
    h = _auth_headers(client)
    f1 = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "mom", "template_type": "momentum", "params": {"window": 10}},
    ).json()["id"]
    f2 = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "vol", "template_type": "volatility", "params": {"window": 10}},
    ).json()["id"]

    _set_level(db_session, 1)  # 升级到 L1

    resp = client.post(
        f"{BASE}/factors/stack",
        headers=h,
        json={
            "name": "多因子组合",
            "components": [
                {"factor_id": f1, "weight": 0.6},
                {"factor_id": f2, "weight": 0.4},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    stack_id = resp.json()["id"]
    assert resp.json()["kind"] == "stack"

    # 预览组合因子: 返回样本统计
    pv = client.post(f"{BASE}/factors/{stack_id}/preview", headers=h)
    assert pv.status_code == 200, pv.text
    stats = pv.json()["stats"]
    assert stats["count"] == 252
    assert "mean" in stats and "std" in stats


def test_preview_template_factor(client):
    h = _auth_headers(client)
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "mom-pv", "template_type": "momentum", "params": {}},
    ).json()["id"]
    pv = client.post(f"{BASE}/factors/{fid}/preview", headers=h)
    assert pv.status_code == 200
    assert pv.json()["kind"] == "template"


def test_list_and_delete_factor(client):
    h = _auth_headers(client)
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "to-delete", "template_type": "volatility", "params": {}},
    ).json()["id"]
    assert len(client.get(f"{BASE}/factors", headers=h).json()) == 1
    assert client.delete(f"{BASE}/factors/{fid}", headers=h).status_code == 204
    assert len(client.get(f"{BASE}/factors", headers=h).json()) == 0


def test_factors_require_auth(client):
    assert client.get(f"{BASE}/factors").status_code == 403

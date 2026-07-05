"""机构团队研究提醒汇总测试。"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"

OWNER = {"email": "attn1@quantlab.ai", "username": "attnowner", "password": "s3cret-pass"}
MEMBER = {"email": "attn2@quantlab.ai", "username": "attnmember", "password": "s3cret-pass"}


def _auth(client, user=OWNER) -> dict:
    client.post(f"{BASE}/auth/register", json=user)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": user["username"], "password": user["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_org_team_attention_rollup_empty(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)
    seed_sample_market_data(db_session)

    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Alert Desk"}).json()["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )

    resp = client.get(f"{BASE}/orgs/{org_id}/research/attention-alerts", headers=h_owner)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["member_count"] == 2
    assert body["total_alerts"] == 0
    assert body["items"] == []
    assert body["summary"]

    denied = client.get(f"{BASE}/orgs/{org_id}/research/attention-alerts", headers=h_member)
    assert denied.status_code == 403


def test_org_team_attention_rollup_with_member_project(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)
    seed_sample_market_data(db_session)

    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Coach Org"}).json()["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )

    proj = client.post(
        f"{BASE}/projects",
        headers=h_member,
        json={"title": "member-p", "symbol": "RB"},
    ).json()
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h_member,
        json={
            "name": "m-mom",
            "template_type": "momentum",
            "params": {"window": 20},
            "project_id": proj["id"],
        },
    ).json()["id"]
    client.post(f"{BASE}/backtests", headers=h_member, json={"factor_id": fid, "symbol": "RB"})
    client.post(
        f"{BASE}/validations",
        headers=h_member,
        json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4},
    )

    resp = client.get(f"{BASE}/orgs/{org_id}/research/attention-alerts", headers=h_owner)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["member_count"] >= 1
    if body["total_alerts"] > 0:
        item = body["items"][0]
        assert item["username"] == MEMBER["username"]
        assert item["kind"] in ("regime_shift", "weak_regime_fit", "paper_decay")
        assert item["cta_path"]

"""研究机构 / 团队因子库测试。"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"

OWNER = {"email": "org1@quantlab.ai", "username": "orgowner", "password": "s3cret-pass"}
MEMBER = {"email": "org2@quantlab.ai", "username": "orgmember", "password": "s3cret-pass"}


def _auth(client, user=OWNER) -> dict:
    client.post(f"{BASE}/auth/register", json=user)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": user["username"], "password": user["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _make_factor(client, h, name="mom") -> str:
    return client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": name, "template_type": "momentum", "params": {"window": 10}},
    ).json()["id"]


def test_create_org_and_list(client, db_session):
    h = _auth(client)
    resp = client.post(f"{BASE}/orgs", headers=h, json={"name": "Alpha Research"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Alpha Research"
    assert body["my_role"] == "owner"
    assert body["member_count"] == 1

    listed = client.get(f"{BASE}/orgs", headers=h)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_share_factor_and_org_catalog(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)
    seed_sample_market_data(db_session)

    org = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Desk A"}).json()
    org_id = org["id"]

    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )

    fid = _make_factor(client, h_owner, "desk-mom")
    client.post(
        f"{BASE}/backtests",
        headers=h_owner,
        json={"factor_id": fid, "symbol": "RB", "fee_rate": 0.0005, "slippage_bps": 1.0},
    )
    share = client.post(
        f"{BASE}/orgs/{org_id}/factors/{fid}/share",
        headers=h_owner,
        json={"note": "team alpha"},
    )
    assert share.status_code == 200, share.text

    listed = client.get(f"{BASE}/orgs/{org_id}/factors", headers=h_member)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["factor_name"] == "desk-mom"

    catalog = client.get(
        f"{BASE}/orgs/{org_id}/catalog", headers=h_member, params={"symbol": "RB"}
    )
    assert catalog.status_code == 200, catalog.text
    cat = catalog.json()
    assert len(cat["factors"]) == 1
    assert cat["factors"][0]["share_note"] == "team alpha"


def test_non_member_denied(client, db_session):
    h_owner = _auth(client, OWNER)
    h_stranger = _auth(client, {"email": "x@y.com", "username": "stranger", "password": "s3cret-pass"})
    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Private Desk"}).json()["id"]
    resp = client.get(f"{BASE}/orgs/{org_id}", headers=h_stranger)
    assert resp.status_code == 403


def test_org_invite_preview_and_accept(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)
    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Invite Desk"}).json()["id"]

    created = client.post(
        f"{BASE}/orgs/{org_id}/invites",
        headers=h_owner,
        json={"role": "member", "expires_in_days": 7, "max_uses": 2},
    )
    assert created.status_code == 201, created.text
    token = created.json()["token"]
    assert created.json()["invite_path"].endswith(token)

    preview = client.get(f"{BASE}/orgs/invites/{token}", headers=h_member)
    assert preview.status_code == 200, preview.text
    assert preview.json()["org_name"] == "Invite Desk"
    assert preview.json()["already_member"] is False

    accepted = client.post(f"{BASE}/orgs/invites/{token}/accept", headers=h_member)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["my_role"] == "member"

    detail = client.get(f"{BASE}/orgs/{org_id}", headers=h_member)
    assert detail.status_code == 200
    assert detail.json()["member_count"] == 2

    preview_again = client.get(f"{BASE}/orgs/invites/{token}", headers=h_member)
    assert preview_again.status_code == 200
    assert preview_again.json()["already_member"] is True


def test_non_admin_cannot_create_invite(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)
    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Admin Only"}).json()["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )
    resp = client.post(
        f"{BASE}/orgs/{org_id}/invites",
        headers=h_member,
        json={"role": "member", "expires_in_days": 7, "max_uses": 1},
    )
    assert resp.status_code == 403

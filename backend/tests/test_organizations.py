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


def test_update_member_role_and_remove(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)
    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Gov Desk"}).json()["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )
    members = client.get(f"{BASE}/orgs/{org_id}/members", headers=h_owner).json()
    member_id = next(m["user_id"] for m in members if m["username"] == MEMBER["username"])

    updated = client.patch(
        f"{BASE}/orgs/{org_id}/members/{member_id}",
        headers=h_owner,
        json={"role": "viewer"},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "viewer"

    activity = client.get(f"{BASE}/orgs/{org_id}/activity", headers=h_owner)
    assert activity.status_code == 200
    assert any(a["action"] == "org.member.role" for a in activity.json())

    removed = client.delete(f"{BASE}/orgs/{org_id}/members/{member_id}", headers=h_owner)
    assert removed.status_code == 204
    members_after = client.get(f"{BASE}/orgs/{org_id}/members", headers=h_owner).json()
    assert all(m["username"] != MEMBER["username"] for m in members_after)


def test_org_sso_email_domains(client, db_session):
    h_owner = _auth(client, OWNER)
    outsider = {"email": "outsider@gmail.com", "username": "gmailuser", "password": "s3cret-pass"}
    corp_user = {"email": "alice@corp.com", "username": "corpuser", "password": "s3cret-pass"}
    h_outsider = _auth(client, outsider)
    h_corp = _auth(client, corp_user)

    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Corp Desk"}).json()["id"]

    get_empty = client.get(f"{BASE}/orgs/{org_id}/sso-domains", headers=h_owner)
    assert get_empty.status_code == 200
    assert get_empty.json()["domains"] == []

    set_domains = client.put(
        f"{BASE}/orgs/{org_id}/sso-domains",
        headers=h_owner,
        json={"domains": ["corp.com", "CORP.COM", ""]},
    )
    assert set_domains.status_code == 200
    assert set_domains.json()["domains"] == ["corp.com"]

    denied_add = client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": outsider["username"], "role": "member"},
    )
    assert denied_add.status_code == 422

    invite = client.post(
        f"{BASE}/orgs/{org_id}/invites",
        headers=h_owner,
        json={"role": "member", "expires_in_days": 3, "max_uses": 5},
    ).json()
    denied_accept = client.post(
        f"{BASE}/orgs/invites/{invite['token']}/accept",
        headers=h_outsider,
    )
    assert denied_accept.status_code == 422

    accepted = client.post(
        f"{BASE}/orgs/invites/{invite['token']}/accept",
        headers=h_corp,
    )
    assert accepted.status_code == 200

    ok_add = client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": corp_user["username"], "role": "member"},
    )
    assert ok_add.status_code == 200, ok_add.text


def test_org_execution_orders_admin_view(client, db_session):
    from backend.app.models.user import User, UserLevel
    from backend.app.services import membership_service as ms
    from backend.app.services.market_data import seed_sample_market_data
    from sqlalchemy import select

    h_owner = _auth(client, OWNER)
    trader = {"email": "trader@quantlab.ai", "username": "orgtrader", "password": "s3cret-pass"}
    h_trader = _auth(client, trader)
    seed_sample_market_data(db_session)

    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Exec Desk"}).json()["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": trader["username"], "role": "member"},
    )

    user = db_session.execute(select(User).where(User.username == trader["username"])).scalar_one()
    user.level = UserLevel.L4
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    client.post(
        f"{BASE}/execution/paper/orders",
        headers=h_trader,
        json={"symbol": "RB", "side": "buy", "notional_cny": 22000, "channel": "qmt", "acknowledge_risk": True},
    )

    listed = client.get(f"{BASE}/orgs/{org_id}/execution/orders", headers=h_owner)
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert len(rows) >= 1
    assert rows[0]["username"] == trader["username"]
    assert rows[0]["channel"] == "qmt"

    denied = client.get(f"{BASE}/orgs/{org_id}/execution/orders", headers=h_trader)
    assert denied.status_code == 403


def test_org_execution_batch_refresh(client, db_session, monkeypatch):
    from backend.app.models.user import User, UserLevel
    from backend.app.services import membership_service as ms
    from sqlalchemy import select

    monkeypatch.setattr(
        "backend.app.services.execution_service.fetch_gateway_order_status",
        lambda **_: "filled",
    )

    h_owner = _auth(client, OWNER)
    trader = {"email": "trader2@quantlab.ai", "username": "orgtrader2", "password": "s3cret-pass"}
    h_trader = _auth(client, trader)

    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Poll Desk"}).json()["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": trader["username"], "role": "member"},
    )

    user = db_session.execute(select(User).where(User.username == trader["username"])).scalar_one()
    user.level = UserLevel.L4
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    client.post(
        f"{BASE}/execution/paper/orders",
        headers=h_trader,
        json={"symbol": "RB", "side": "buy", "notional_cny": 11000, "channel": "qmt", "acknowledge_risk": True},
    )

    result = client.post(f"{BASE}/orgs/{org_id}/execution/refresh", headers=h_owner)
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["checked"] >= 1
    assert body["updated"] >= 1

    listed = client.get(f"{BASE}/orgs/{org_id}/execution/orders", headers=h_owner).json()
    assert listed[0]["status"] == "filled"

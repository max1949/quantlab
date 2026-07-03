"""机构团队订阅与计费测试。"""

from __future__ import annotations

from backend.app.services import membership_service as ms
from backend.app.services import org_billing_service as obs

BASE = "/api/v1"

OWNER = {"email": "bill1@quantlab.ai", "username": "billowner", "password": "s3cret-pass"}
MEMBER = {"email": "bill2@quantlab.ai", "username": "billmember", "password": "s3cret-pass"}


def _auth(client, user=OWNER) -> dict:
    client.post(f"{BASE}/auth/register", json=user)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": user["username"], "password": user["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_org_subscription_inherits_tier(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)

    org = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Billing Desk"}).json()
    org_id = org["id"]

    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )

    rc = ms.create_redeem_code(
        db_session,
        tier=ms.TIER_PLUS,
        plan_code="org_plus_monthly",
        kind="org",
        seats=5,
    )

    redeem = client.post(
        f"{BASE}/orgs/{org_id}/billing/redeem",
        headers=h_owner,
        json={"code": rc.code},
    )
    assert redeem.status_code == 200, redeem.text
    assert redeem.json()["tier"] == 1
    assert redeem.json()["seats"] == 5

    history = client.get(f"{BASE}/orgs/{org_id}/billing/history", headers=h_owner)
    assert history.status_code == 200, history.text
    rows = history.json()
    assert len(rows) >= 1
    assert rows[0]["scope"] == "org"
    assert rows[0]["event"] == "redeem"
    assert rows[0]["seats"] == 5

    billing = client.get(f"{BASE}/orgs/{org_id}/billing", headers=h_owner)
    assert billing.status_code == 200
    assert billing.json()["is_paid"] is True
    assert billing.json()["tier"] == 1

    member_ent = client.get(f"{BASE}/billing/entitlements", headers=h_member)
    assert member_ent.status_code == 200
    assert member_ent.json()["tier"] == 1

    sub = client.get(f"{BASE}/billing/me", headers=h_member)
    assert sub.json()["org_tier"] == 1
    assert sub.json()["org_benefit"] is True


def test_org_redeem_owner_only(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)

    org = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Billing Desk 2"}).json()
    org_id = org["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )

    rc = ms.create_redeem_code(
        db_session,
        tier=ms.TIER_PLUS,
        plan_code="org_plus_monthly",
        kind="org",
        seats=5,
    )

    denied = client.post(
        f"{BASE}/orgs/{org_id}/billing/redeem",
        headers=h_member,
        json={"code": rc.code},
    )
    assert denied.status_code == 422


def test_org_checkout_not_configured(client, db_session):
    h_owner = _auth(client, OWNER)
    org = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Checkout Org"}).json()

    resp = client.post(
        f"{BASE}/orgs/{org['id']}/billing/checkout",
        headers=h_owner,
        json={"plan_code": "org_plus_monthly"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is False
    assert body["pay_url"] is None


def test_personal_code_rejected_for_org(client, db_session):
    h_owner = _auth(client, OWNER)
    org = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Wrong Code Org"}).json()

    rc = ms.create_redeem_code(db_session, tier=ms.TIER_PLUS, plan_code="plus_monthly")
    resp = client.post(
        f"{BASE}/orgs/{org['id']}/billing/redeem",
        headers=h_owner,
        json={"code": rc.code},
    )
    assert resp.status_code == 422


def test_seat_limit_blocks_over_free_quota(client, db_session):
    from backend.app.services.org_billing_service import FREE_SEATS

    h_owner = _auth(client, OWNER)
    org = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Seat Org"}).json()
    org_id = org["id"]

    # owner 占 1 席; 免费额度 FREE_SEATS。逐个添加成员直到超额被拦。
    created = 0
    last_status = 200
    for i in range(FREE_SEATS + 2):
        uname = f"seatuser{i}"
        client.post(
            f"{BASE}/auth/register",
            json={"email": f"{uname}@x.com", "username": uname, "password": "s3cret-pass"},
        )
        resp = client.post(
            f"{BASE}/orgs/{org_id}/members",
            headers=h_owner,
            json={"username": uname, "role": "member"},
        )
        last_status = resp.status_code
        if resp.status_code == 201 or resp.status_code == 200:
            created += 1
        else:
            break

    # owner(1) + created 不应超过 FREE_SEATS, 且最终一次是 422。
    assert 1 + created <= FREE_SEATS
    assert last_status == 422


def test_seat_limit_expands_with_team_plan(client, db_session):
    h_owner = _auth(client, OWNER)
    org = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Seat Grow Org"}).json()
    org_id = org["id"]

    rc = ms.create_redeem_code(
        db_session, tier=ms.TIER_PLUS, plan_code="org_plus_monthly", kind="org", seats=5
    )
    client.post(f"{BASE}/orgs/{org_id}/billing/redeem", headers=h_owner, json={"code": rc.code})

    billing = client.get(f"{BASE}/orgs/{org_id}/billing", headers=h_owner).json()
    assert billing["seats"] == 5

    # 现在可以加到 5 席 (owner + 4)。
    for i in range(4):
        uname = f"growuser{i}"
        client.post(
            f"{BASE}/auth/register",
            json={"email": f"{uname}@x.com", "username": uname, "password": "s3cret-pass"},
        )
        resp = client.post(
            f"{BASE}/orgs/{org_id}/members",
            headers=h_owner,
            json={"username": uname, "role": "member"},
        )
        assert resp.status_code in (200, 201), resp.text


def test_grant_org_subscription_service(db_session):
    from backend.app.models.organization import OrgMember, ResearchOrg
    from backend.app.models.user import User

    user = User(email="svc@x.com", username="svcuser", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    org = ResearchOrg(name="Svc Org", slug="svc-org", owner_id=user.id)
    db_session.add(org)
    db_session.flush()
    db_session.add(OrgMember(org_id=org.id, user_id=user.id, role="owner"))
    db_session.commit()

    obs.grant_org_subscription(
        db_session,
        org.id,
        tier=2,
        period_days=30,
        plan_code="org_pro_monthly",
        seats=20,
    )
    assert obs.org_tier(db_session, org.id) == 2
    assert obs.org_tiers_for_user(db_session, user.id) == 2


def test_personal_billing_history(client, db_session):
    h = _auth(client)
    rc = ms.create_redeem_code(db_session, tier=ms.TIER_PLUS, plan_code="plus_monthly")
    client.post(f"{BASE}/billing/redeem", headers=h, json={"code": rc.code})
    history = client.get(f"{BASE}/billing/history", headers=h)
    assert history.status_code == 200, history.text
    rows = history.json()
    assert len(rows) >= 1
    assert rows[0]["scope"] == "personal"


def test_personal_billing_csv_export(client, db_session):
    h = _auth(client)
    rc = ms.create_redeem_code(db_session, tier=ms.TIER_PLUS, plan_code="plus_monthly")
    client.post(f"{BASE}/billing/redeem", headers=h, json={"code": rc.code})
    resp = client.get(f"{BASE}/billing/history/export", headers=h)
    assert resp.status_code == 200, resp.text
    assert "text/csv" in resp.headers.get("content-type", "")
    body = resp.text.lstrip("\ufeff")
    assert "plan_code" in body.splitlines()[0]
    assert "plus_monthly" in body


def test_personal_billing_invoice_pdf(client, db_session):
    h = _auth(client)
    rc = ms.create_redeem_code(db_session, tier=ms.TIER_PLUS, plan_code="plus_monthly")
    client.post(f"{BASE}/billing/redeem", headers=h, json={"code": rc.code})
    rows = client.get(f"{BASE}/billing/history", headers=h).json()
    resp = client.get(f"{BASE}/billing/history/{rows[0]['id']}/invoice.pdf", headers=h)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_org_billing_csv_export(client, db_session):
    h_owner = _auth(client, OWNER)
    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "CSV Org"}).json()["id"]
    rc = ms.create_redeem_code(
        db_session,
        tier=ms.TIER_PLUS,
        plan_code="org_plus_monthly",
        kind="org",
        seats=5,
    )
    client.post(
        f"{BASE}/orgs/{org_id}/billing/redeem",
        headers=h_owner,
        json={"code": rc.code},
    )
    resp = client.get(f"{BASE}/orgs/{org_id}/billing/history/export", headers=h_owner)
    assert resp.status_code == 200, resp.text
    assert "text/csv" in resp.headers.get("content-type", "")
    body = resp.text.lstrip("\ufeff")
    assert "org_plus_monthly" in body


def test_org_billing_invoice_pdf(client, db_session):
    h_owner = _auth(client, OWNER)
    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "PDF Org"}).json()["id"]
    rc = ms.create_redeem_code(
        db_session,
        tier=ms.TIER_PLUS,
        plan_code="org_plus_monthly",
        kind="org",
        seats=5,
    )
    client.post(
        f"{BASE}/orgs/{org_id}/billing/redeem",
        headers=h_owner,
        json={"code": rc.code},
    )
    rows = client.get(f"{BASE}/orgs/{org_id}/billing/history", headers=h_owner).json()
    resp = client.get(
        f"{BASE}/orgs/{org_id}/billing/history/{rows[0]['id']}/invoice.pdf",
        headers=h_owner,
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_org_billing_profile_and_invoice_header(client, db_session):
    from backend.app.services import billing_ledger_service as bls

    h_owner = _auth(client, OWNER)
    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Invoice Org"}).json()["id"]

    empty = client.get(f"{BASE}/orgs/{org_id}/billing/profile", headers=h_owner)
    assert empty.status_code == 200
    assert empty.json()["configured"] is False

    put = client.put(
        f"{BASE}/orgs/{org_id}/billing/profile",
        headers=h_owner,
        json={
            "company_name": "QuantLab Research Ltd",
            "tax_id": "91310000MA1K12345X",
            "address": "Shanghai, China",
        },
    )
    assert put.status_code == 200, put.text
    profile = put.json()
    assert profile["configured"] is True
    assert profile["company_name"] == "QuantLab Research Ltd"

    rc = ms.create_redeem_code(
        db_session,
        tier=ms.TIER_PLUS,
        plan_code="org_plus_monthly",
        kind="org",
        seats=5,
    )
    client.post(
        f"{BASE}/orgs/{org_id}/billing/redeem",
        headers=h_owner,
        json={"code": rc.code},
    )
    rows = client.get(f"{BASE}/orgs/{org_id}/billing/history", headers=h_owner).json()
    resp = client.get(
        f"{BASE}/orgs/{org_id}/billing/history/{rows[0]['id']}/invoice.pdf",
        headers=h_owner,
    )
    assert resp.status_code == 200, resp.text
    pdf = bls.render_invoice_pdf(rows[0], billing_profile=profile)
    assert b"QuantLab Research Ltd" in pdf
    assert b"91310000MA1K12345X" in pdf

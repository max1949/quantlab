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

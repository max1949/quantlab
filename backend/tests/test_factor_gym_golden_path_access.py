"""E2E: Factor Gym Golden Path under Open Beta.

REAL_USER_GOLDEN_PATH_REACHABILITY still required before claiming First Value.
PRODUCT_FIRST_VALUE stays UNPROVEN until reality evidence closes.
"""

from __future__ import annotations

BASE = "/api/v1"


def _register(client, email: str, username: str):
    client.post(
        f"{BASE}/auth/register",
        json={"email": email, "username": username, "password": "s3cret-pass"},
    )
    r = client.post(
        f"{BASE}/auth/login",
        json={"identifier": username, "password": "s3cret-pass"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _save(settings):
    return (
        settings.quantlab_factor_gym,
        getattr(settings, "quantlab_factor_gym_open_beta", True),
        getattr(settings, "quantlab_factor_gym_kill", False),
        settings.quantlab_factor_gym_test_allowlist,
        settings.quantlab_factor_gym_test_token,
    )


def _restore(settings, prev):
    (
        settings.quantlab_factor_gym,
        settings.quantlab_factor_gym_open_beta,
        settings.quantlab_factor_gym_kill,
        settings.quantlab_factor_gym_test_allowlist,
        settings.quantlab_factor_gym_test_token,
    ) = prev


def _golden_path(client, headers):
    st = client.get(f"{BASE}/factor-gym/status", headers=headers)
    assert st.status_code == 200
    assert st.json()["FACTOR_GYM_ACCESS_ALLOWED"] is True
    assert st.json()["allowed"] is True
    assert "测试版" in st.json()["label"]

    idea = client.post(
        f"{BASE}/factor-gym/ideas",
        headers=headers,
        json={"idea": "连续下跌几天后是不是更容易反弹"},
    )
    assert idea.status_code == 200, idea.text
    body = idea.json()
    assert body["hypothesis_id"]
    assert body["memory_check"]["next_best_research_action"]
    hid = body["hypothesis_id"]
    hit = body["memory_check"].get("hit_id")

    sealed = client.post(
        f"{BASE}/factor-gym/hypotheses/seal",
        headers=headers,
        json={
            "hypothesis_id": hid,
            "research_question": body["research_question"],
            "economic_rationale": "mean reversion after drawdown",
        },
    )
    assert sealed.status_code == 200, sealed.text

    if hit:
        dec = client.post(
            f"{BASE}/factor-gym/memory-decision",
            headers=headers,
            json={"hit_id": hit, "decision": "continue", "hypothesis_id": hid},
        )
        assert dec.status_code == 200, dec.text

    run = client.post(
        f"{BASE}/factor-gym/experiments/run",
        headers=headers,
        json={
            "hypothesis_id": hid,
            "predicted_direction": "positive",
            "predicted_strength": "moderate",
            "memory_hit_id": hit,
        },
    )
    assert run.status_code == 200, run.text
    result = run.json()
    assert result["status"] in ("PASS", "BORDERLINE", "FAIL", "KILL")
    assert result["why"]
    assert result["next_best_action"]
    assert result.get("experiment_id")
    return result


def test_case1_open_beta_authenticated_golden_path(client, monkeypatch, tmp_path):
    """CASE 1: Open Beta + any authenticated user → full Idea→…→Result."""
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = _save(settings)
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_open_beta = True
    settings.quantlab_factor_gym_kill = False
    settings.quantlab_factor_gym_test_allowlist = ""
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, "case1@quantlab.ai", "case1")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.json()["mode"] == "open_beta"
        _golden_path(client, headers)
        vault = client.get(f"{BASE}/factor-gym/vault", headers=headers)
        assert vault.status_code == 200
    finally:
        _restore(settings, prev)


def test_case2_kill_switch_denies(client):
    """CASE 2: Emergency kill → authenticated denied."""
    from backend.app.core.config import get_settings

    settings = get_settings()
    prev = _save(settings)
    settings.quantlab_factor_gym_open_beta = True
    settings.quantlab_factor_gym_kill = True
    settings.captcha_disabled = True
    try:
        headers = _register(client, "killed@quantlab.ai", "killed2")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.json()["FACTOR_GYM_ACCESS_ALLOWED"] is False
        ideas = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=headers,
            json={"idea": "随便一个市场想法即可"},
        )
        assert ideas.status_code == 403
    finally:
        _restore(settings, prev)


def test_case3_anonymous_denied(client):
    """CASE 3: Anonymous → API denied."""
    st = client.get(f"{BASE}/factor-gym/status")
    assert st.status_code in (401, 403)
    ideas = client.post(
        f"{BASE}/factor-gym/ideas",
        json={"idea": "随便一个市场想法即可"},
    )
    assert ideas.status_code in (401, 403)


def test_case4_legacy_global_on_still_works(client, monkeypatch, tmp_path):
    """CASE 4: Legacy QUANTLAB_FACTOR_GYM=true with open_beta off still allows auth users."""
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = _save(settings)
    settings.quantlab_factor_gym = True
    settings.quantlab_factor_gym_open_beta = False
    settings.quantlab_factor_gym_kill = False
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, "globalon@quantlab.ai", "globalon")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.json()["FACTOR_GYM_ACCESS_ALLOWED"] is True
        assert st.json()["mode"] == "global"
        assert "测试版" in st.json()["label"]
        _golden_path(client, headers)
    finally:
        _restore(settings, prev)

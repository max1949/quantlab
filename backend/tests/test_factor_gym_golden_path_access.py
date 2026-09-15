"""E2E: Factor Gym Golden Path under controlled entry (global flag OFF).

REAL_USER_ENTRY_REACHABILITY alone is insufficient —
REAL_USER_GOLDEN_PATH_REACHABILITY must also PASS before human sessions.
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


def _golden_path(client, headers):
    st = client.get(f"{BASE}/factor-gym/status", headers=headers)
    assert st.status_code == 200
    assert st.json()["allowed"] is True
    assert st.json()["enabled"] is True

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


def test_case1_allowlist_full_golden_path(client, monkeypatch, tmp_path):
    """CASE 1: Global OFF + allowlist user → full Idea→…→Result."""
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = (settings.quantlab_factor_gym, settings.quantlab_factor_gym_test_allowlist, settings.quantlab_factor_gym_test_token)
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_test_allowlist = "case1@quantlab.ai,case1"
    settings.quantlab_factor_gym_test_token = ""
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, "case1@quantlab.ai", "case1")
        _golden_path(client, headers)
        vault = client.get(f"{BASE}/factor-gym/vault", headers=headers)
        assert vault.status_code == 200
    finally:
        settings.quantlab_factor_gym, settings.quantlab_factor_gym_test_allowlist, settings.quantlab_factor_gym_test_token = prev


def test_case2_test_token_full_golden_path(client, monkeypatch, tmp_path):
    """CASE 2: Global OFF + valid test token → full Golden Path."""
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = (settings.quantlab_factor_gym, settings.quantlab_factor_gym_test_allowlist, settings.quantlab_factor_gym_test_token)
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_test_allowlist = ""
    settings.quantlab_factor_gym_test_token = "case2-gym-secret"
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, "case2@quantlab.ai", "case2")
        headers = {**headers, "X-Factor-Gym-Test-Token": "case2-gym-secret"}
        _golden_path(client, headers)
    finally:
        settings.quantlab_factor_gym, settings.quantlab_factor_gym_test_allowlist, settings.quantlab_factor_gym_test_token = prev


def test_case3_ordinary_user_denied(client, monkeypatch):
    """CASE 3: Global OFF + ordinary user → status denied + API 403."""
    from backend.app.core.config import get_settings

    settings = get_settings()
    prev = (settings.quantlab_factor_gym, settings.quantlab_factor_gym_test_allowlist, settings.quantlab_factor_gym_test_token)
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_test_allowlist = "someone-else"
    settings.quantlab_factor_gym_test_token = "not-for-you"
    settings.captcha_disabled = True
    try:
        headers = _register(client, "normie@quantlab.ai", "normie")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.json()["allowed"] is False
        assert st.json()["enabled"] is False
        ideas = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=headers,
            json={"idea": "随便一个市场想法即可"},
        )
        assert ideas.status_code == 403
        run = client.post(
            f"{BASE}/factor-gym/experiments/run",
            headers=headers,
            json={
                "hypothesis_id": "HYP-X",
                "predicted_direction": "unclear",
            },
        )
        assert run.status_code == 403
    finally:
        settings.quantlab_factor_gym, settings.quantlab_factor_gym_test_allowlist, settings.quantlab_factor_gym_test_token = prev


def test_case4_global_on_preserved(client, monkeypatch, tmp_path):
    """CASE 4: Global ON → existing intended behavior preserved."""
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = settings.quantlab_factor_gym
    settings.quantlab_factor_gym = True
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, "globalon@quantlab.ai", "globalon")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.json()["mode"] == "global"
        assert st.json()["test_entry"] is False
        _golden_path(client, headers)
    finally:
        settings.quantlab_factor_gym = prev

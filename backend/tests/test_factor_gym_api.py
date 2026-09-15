"""Factor Gym API — feature flag + golden path smoke."""

from __future__ import annotations

BASE = "/api/v1"


def _register(client, email: str = "gymuser@quantlab.ai", username: str = "gymuser"):
    client.post(
        f"{BASE}/auth/register",
        json={"email": email, "username": username, "password": "s3cret-pass"},
    )
    r = client.post(
        f"{BASE}/auth/login",
        json={"identifier": username, "password": "s3cret-pass"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_factor_gym_disabled_by_default(client):
    headers = _register(client)
    st = client.get(f"{BASE}/factor-gym/status", headers=headers)
    assert st.status_code == 200
    body = st.json()
    assert body["enabled"] is False
    assert body["allowed"] is False
    assert body["owner_token_fallback"] == "DENY"
    assert body.get("public_rollout") is False
    assert "受邀" in (body.get("denied_detail") or "")
    blocked = client.post(f"{BASE}/factor-gym/ideas", headers=headers, json={"idea": "动量会延续"})
    assert blocked.status_code == 403
    assert "受邀" in blocked.json()["detail"]


def test_factor_gym_allowlist_test_entry(client, monkeypatch, tmp_path):
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev_flag = settings.quantlab_factor_gym
    prev_allow = settings.quantlab_factor_gym_test_allowlist
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_test_allowlist = "gymallow@quantlab.ai,gymallow"
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, email="gymallow@quantlab.ai", username="gymallow")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.status_code == 200
        body = st.json()
        assert body["enabled"] is True
        assert body["allowed"] is True
        assert body["test_entry"] is True
        assert "测试版" in body["label"]
        assert st.headers.get("cache-control", "").lower().startswith("no-store")
        idea = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=headers,
            json={"idea": "连续下跌后更容易反弹吗"},
        )
        assert idea.status_code == 200, idea.text
        # non-allowlisted user still blocked
        other = _register(client, email="outsider@quantlab.ai", username="outsider")
        st2 = client.get(f"{BASE}/factor-gym/status", headers=other)
        assert st2.json()["enabled"] is False
        blocked = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=other,
            json={"idea": "连续下跌后更容易反弹吗"},
        )
        assert blocked.status_code == 403
    finally:
        settings.quantlab_factor_gym = prev_flag
        settings.quantlab_factor_gym_test_allowlist = prev_allow


def test_factor_gym_test_token_header(client, monkeypatch, tmp_path):
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev_flag = settings.quantlab_factor_gym
    prev_tok = settings.quantlab_factor_gym_test_token
    prev_allow = settings.quantlab_factor_gym_test_allowlist
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_test_allowlist = ""
    settings.quantlab_factor_gym_test_token = "ql-gym-test-secret"
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, email="tokuser@quantlab.ai", username="tokuser")
        denied = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert denied.json()["enabled"] is False
        headers2 = {**headers, "X-Factor-Gym-Test-Token": "ql-gym-test-secret"}
        st = client.get(f"{BASE}/factor-gym/status", headers=headers2)
        assert st.json()["enabled"] is True
        assert st.json()["mode"] == "test_token"
        idea = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=headers2,
            json={"idea": "涨多了会不会继续涨"},
        )
        assert idea.status_code == 200, idea.text
    finally:
        settings.quantlab_factor_gym = prev_flag
        settings.quantlab_factor_gym_test_token = prev_tok
        settings.quantlab_factor_gym_test_allowlist = prev_allow


def test_factor_gym_golden_path_when_enabled(client, monkeypatch, tmp_path):
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = settings.quantlab_factor_gym
    settings.quantlab_factor_gym = True
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, email="gymon@quantlab.ai", username="gymon")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.json()["enabled"] is True

        idea = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=headers,
            json={"idea": "上涨之后更容易继续上涨一段时间"},
        )
        assert idea.status_code == 200, idea.text
        assert "memory_check" in idea.json()
        assert idea.json()["memory_check"]["what_we_already_know"]
        assert idea.json()["memory_check"]["next_best_research_action"]
        assert idea.json()["memory_check"]["semantic_similarity"] == "DEFER"
        hid = idea.json()["hypothesis_id"]

        sealed = client.post(
            f"{BASE}/factor-gym/hypotheses/seal",
            headers=headers,
            json={
                "hypothesis_id": hid,
                "research_question": idea.json()["research_question"],
                "economic_rationale": "trend persistence",
            },
        )
        assert sealed.status_code == 200, sealed.text

        run = client.post(
            f"{BASE}/factor-gym/experiments/run",
            headers=headers,
            json={
                "hypothesis_id": hid,
                "predicted_direction": "positive",
                "predicted_strength": "moderate",
                "memory_hit_id": idea.json()["memory_check"].get("hit_id"),
            },
        )
        assert run.status_code == 200, run.text
        body = run.json()
        assert body["status"] in ("PASS", "BORDERLINE", "FAIL", "KILL")
        assert body["next_best_action"]
        assert body["why"]
        assert "metrics_folded" in body
    finally:
        settings.quantlab_factor_gym = prev

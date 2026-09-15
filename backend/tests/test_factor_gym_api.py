"""Factor Gym API — Open Beta + kill switch + golden path smoke."""

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


def _save_beta(settings):
    return (
        settings.quantlab_factor_gym,
        getattr(settings, "quantlab_factor_gym_open_beta", True),
        getattr(settings, "quantlab_factor_gym_kill", False),
        settings.quantlab_factor_gym_test_allowlist,
        settings.quantlab_factor_gym_test_token,
    )


def _restore_beta(settings, prev):
    (
        settings.quantlab_factor_gym,
        settings.quantlab_factor_gym_open_beta,
        settings.quantlab_factor_gym_kill,
        settings.quantlab_factor_gym_test_allowlist,
        settings.quantlab_factor_gym_test_token,
    ) = prev


def test_factor_gym_open_beta_authenticated(client, monkeypatch, tmp_path):
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = _save_beta(settings)
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_open_beta = True
    settings.quantlab_factor_gym_kill = False
    settings.quantlab_factor_gym_test_allowlist = ""
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, email="beta@quantlab.ai", username="betauser")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.status_code == 200
        body = st.json()
        assert body["FACTOR_GYM_ACCESS_ALLOWED"] is True
        assert body["allowed"] is True
        assert body["open_beta"] is True
        assert body["mode"] == "open_beta"
        assert body["enabled"] is False
        assert "测试版" in body["label"]
        assert "受邀" not in (body.get("denied_detail") or "")
        assert body.get("public_rollout") is False
        assert st.headers.get("cache-control", "").lower().startswith("no-store")
        idea = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=headers,
            json={"idea": "连续下跌后更容易反弹吗"},
        )
        assert idea.status_code == 200, idea.text
    finally:
        _restore_beta(settings, prev)


def test_factor_gym_kill_denies_authenticated(client):
    from backend.app.core.config import get_settings

    settings = get_settings()
    prev = _save_beta(settings)
    settings.quantlab_factor_gym_open_beta = True
    settings.quantlab_factor_gym_kill = True
    settings.captcha_disabled = True
    try:
        headers = _register(client, email="killed@quantlab.ai", username="killeduser")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.json()["FACTOR_GYM_ACCESS_ALLOWED"] is False
        assert st.json()["mode"] == "killed"
        blocked = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=headers,
            json={"idea": "动量会延续"},
        )
        assert blocked.status_code == 403
        assert "受邀" not in blocked.json()["detail"]
    finally:
        _restore_beta(settings, prev)


def test_factor_gym_anonymous_status_requires_auth(client):
    st = client.get(f"{BASE}/factor-gym/status")
    assert st.status_code in (401, 403)


def test_factor_gym_qa_token_when_open_beta_off(client, monkeypatch, tmp_path):
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = _save_beta(settings)
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_open_beta = False
    settings.quantlab_factor_gym_kill = False
    settings.quantlab_factor_gym_test_allowlist = ""
    settings.quantlab_factor_gym_test_token = "ql-gym-test-secret"
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, email="tokuser@quantlab.ai", username="tokuser")
        denied = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert denied.json()["FACTOR_GYM_ACCESS_ALLOWED"] is False
        headers2 = {**headers, "X-Factor-Gym-Test-Token": "ql-gym-test-secret"}
        st = client.get(f"{BASE}/factor-gym/status", headers=headers2)
        assert st.json()["FACTOR_GYM_ACCESS_ALLOWED"] is True
        assert st.json()["mode"] == "test_token_qa"
    finally:
        _restore_beta(settings, prev)


def test_factor_gym_golden_path_open_beta(client, monkeypatch, tmp_path):
    from backend.app.core.config import get_settings
    from engine.factor_gym import hypothesis as hyp_mod

    settings = get_settings()
    prev = _save_beta(settings)
    settings.quantlab_factor_gym = False
    settings.quantlab_factor_gym_open_beta = True
    settings.quantlab_factor_gym_kill = False
    settings.captcha_disabled = True
    monkeypatch.setattr(hyp_mod, "DEFAULT_GYM_DIR", tmp_path)
    try:
        headers = _register(client, email="gymon@quantlab.ai", username="gymon")
        st = client.get(f"{BASE}/factor-gym/status", headers=headers)
        assert st.json()["FACTOR_GYM_ACCESS_ALLOWED"] is True

        idea = client.post(
            f"{BASE}/factor-gym/ideas",
            headers=headers,
            json={"idea": "上涨之后更容易继续上涨一段时间"},
        )
        assert idea.status_code == 200, idea.text
        assert "memory_check" in idea.json()
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
    finally:
        _restore_beta(settings, prev)

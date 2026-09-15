"""Factor Gym Open Beta + emergency kill + internal QA fallbacks."""

from __future__ import annotations

from types import SimpleNamespace

from backend.app.services.factor_gym_access import parse_test_allowlist, resolve_factor_gym_access


def _user(**kw):
    base = dict(id=42, email="novice@example.com", username="novice1")
    base.update(kw)
    return SimpleNamespace(**base)


def _settings(**kw):
    base = dict(
        quantlab_factor_gym=False,
        quantlab_factor_gym_open_beta=True,
        quantlab_factor_gym_kill=False,
        quantlab_factor_gym_test_allowlist="",
        quantlab_factor_gym_test_token="",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_parse_allowlist():
    assert parse_test_allowlist("a@x.com, Bob, 99") == {"a@x.com", "bob", "99"}


def test_open_beta_authenticated_allowed():
    out = resolve_factor_gym_access(_user(), settings=_settings())
    assert out["FACTOR_GYM_ACCESS_ALLOWED"] is True
    assert out["allowed"] is True
    assert out["mode"] == "open_beta"
    assert out["test_entry"] is True
    assert out["label"] == "Factor Gym（测试版）"
    assert out["public_rollout"] is False
    assert out["enabled"] is False


def test_open_beta_anonymous_denied():
    out = resolve_factor_gym_access(None, settings=_settings())
    assert out["FACTOR_GYM_ACCESS_ALLOWED"] is False
    assert "登录" in (out.get("denied_detail") or "")


def test_emergency_kill_denies_authenticated():
    out = resolve_factor_gym_access(_user(), settings=_settings(quantlab_factor_gym_kill=True))
    assert out["FACTOR_GYM_ACCESS_ALLOWED"] is False
    assert out["mode"] == "killed"
    assert "关闭" in (out.get("denied_detail") or "")


def test_allowlist_not_required_in_open_beta():
    """Ordinary user (not on allowlist) still allowed under Open Beta."""
    out = resolve_factor_gym_access(
        _user(email="outsider@x.com", username="outsider"),
        settings=_settings(quantlab_factor_gym_test_allowlist="only@x.com"),
    )
    assert out["FACTOR_GYM_ACCESS_ALLOWED"] is True
    assert out["mode"] == "open_beta"


def test_allowlist_qa_when_open_beta_off():
    settings = _settings(
        quantlab_factor_gym_open_beta=False,
        quantlab_factor_gym_test_allowlist="novice@example.com",
    )
    denied = resolve_factor_gym_access(
        _user(email="outsider@x.com", username="outsider"),
        settings=settings,
    )
    assert denied["FACTOR_GYM_ACCESS_ALLOWED"] is False
    ok = resolve_factor_gym_access(_user(), settings=settings)
    assert ok["FACTOR_GYM_ACCESS_ALLOWED"] is True
    assert ok["mode"] == "allowlist_qa"


def test_test_token_qa_when_open_beta_off():
    settings = _settings(
        quantlab_factor_gym_open_beta=False,
        quantlab_factor_gym_test_token="secret-gym-test",
    )
    denied = resolve_factor_gym_access(_user(), test_token="wrong", settings=settings)
    assert denied["FACTOR_GYM_ACCESS_ALLOWED"] is False
    ok = resolve_factor_gym_access(_user(), test_token="secret-gym-test", settings=settings)
    assert ok["FACTOR_GYM_ACCESS_ALLOWED"] is True
    assert ok["mode"] == "test_token_qa"


def test_denied_detail_has_no_invite_copy():
    out = resolve_factor_gym_access(None, settings=_settings(quantlab_factor_gym_open_beta=False))
    detail = out.get("denied_detail") or ""
    assert "受邀" not in detail
    assert "证据系统" not in detail
    assert "QUANTLAB_FACTOR_GYM" not in detail


def test_legacy_flag_allows_when_open_beta_off():
    out = resolve_factor_gym_access(
        _user(),
        settings=_settings(quantlab_factor_gym=True, quantlab_factor_gym_open_beta=False),
    )
    assert out["FACTOR_GYM_ACCESS_ALLOWED"] is True
    assert out["enabled"] is True
    assert out["public_rollout"] is False
    assert "测试版" in out["label"]

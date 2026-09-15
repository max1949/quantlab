"""Controlled Factor Gym test entry — allowlist / token; public flag stays OFF."""

from __future__ import annotations

from types import SimpleNamespace

from backend.app.services.factor_gym_access import parse_test_allowlist, resolve_factor_gym_access


def _user(**kw):
    base = dict(id=42, email="novice@example.com", username="novice1")
    base.update(kw)
    return SimpleNamespace(**base)


def test_parse_allowlist():
    assert parse_test_allowlist("a@x.com, Bob, 99") == {"a@x.com", "bob", "99"}


def test_denied_when_flag_off_and_no_allowlist():
    settings = SimpleNamespace(
        quantlab_factor_gym=False,
        quantlab_factor_gym_test_allowlist="",
        quantlab_factor_gym_test_token="",
    )
    out = resolve_factor_gym_access(_user(), settings=settings)
    assert out["allowed"] is False
    assert out["enabled"] is False
    assert out["public_rollout"] is False


def test_allowlist_email_grants_test_entry():
    settings = SimpleNamespace(
        quantlab_factor_gym=False,
        quantlab_factor_gym_test_allowlist="novice@example.com,other@x.com",
        quantlab_factor_gym_test_token="",
    )
    out = resolve_factor_gym_access(_user(), settings=settings)
    assert out["allowed"] is True
    assert out["test_entry"] is True
    assert out["mode"] == "allowlist"
    assert "测试版" in out["label"]


def test_test_token_grants_access():
    settings = SimpleNamespace(
        quantlab_factor_gym=False,
        quantlab_factor_gym_test_allowlist="",
        quantlab_factor_gym_test_token="secret-gym-test",
    )
    denied = resolve_factor_gym_access(_user(), test_token="wrong", settings=settings)
    assert denied["allowed"] is False
    ok = resolve_factor_gym_access(_user(), test_token="secret-gym-test", settings=settings)
    assert ok["allowed"] is True
    assert ok["mode"] == "test_token"
    assert ok["test_entry"] is True


def test_denied_detail_is_invite_only():
    settings = SimpleNamespace(
        quantlab_factor_gym=False,
        quantlab_factor_gym_test_allowlist="",
        quantlab_factor_gym_test_token="",
    )
    out = resolve_factor_gym_access(_user(), settings=settings)
    assert out["allowed"] is False
    assert "受邀" in (out.get("denied_detail") or "")
    assert "证据系统" not in (out.get("denied_detail") or "")
    assert "QUANTLAB_FACTOR_GYM" not in (out.get("denied_detail") or "")


def test_global_flag_not_marked_public_rollout():
    settings = SimpleNamespace(
        quantlab_factor_gym=True,
        quantlab_factor_gym_test_allowlist="",
        quantlab_factor_gym_test_token="",
    )
    out = resolve_factor_gym_access(_user(), settings=settings)
    assert out["allowed"] is True
    assert out["test_entry"] is False
    assert out["public_rollout"] is False

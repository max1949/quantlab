"""FACTOR_GYM_ACCESS_RESOLVER — single canonical gate for nav, page, and API.

QUANTLAB_FACTOR_GYM=false keeps public/prod default OFF.
Access = GLOBAL_ENABLED OR CONTROLLED_TEST_USER (allowlist) OR VALID_TEST_TOKEN.

Do NOT maintain a second Gate in frontend beyond consuming this resolver's
status payload / API 403. Page visible ≠ capability unless this resolver allows.
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from backend.app.core.config import Settings, get_settings
from backend.app.models.user import User

# Canonical copy for denied callers (nav hidden / direct URL / API).
DENIED_DETAIL_INVITE_ONLY = "该功能目前仅对受邀测试用户开放。"
DENIED_DETAIL_LEGACY = "研究入门路径尚未开启。请使用测试入口或联系管理员。"


def parse_test_allowlist(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def _truthy_env(raw: str | None) -> bool | None:
    if raw is None:
        return None
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _resolve_flag_sources(settings: Settings | None) -> tuple[bool, str, str]:
    """Return (global_flag, allowlist_raw, token_raw).

    When ``settings`` is omitted (live request path), overlay process env so
    allowlist/token updates apply without relying solely on lru_cached Settings.
    Explicit ``settings=`` (unit tests) always wins.
    """
    if settings is not None:
        return (
            bool(getattr(settings, "quantlab_factor_gym", False)),
            getattr(settings, "quantlab_factor_gym_test_allowlist", "") or "",
            getattr(settings, "quantlab_factor_gym_test_token", "") or "",
        )
    s = get_settings()
    env_flag = _truthy_env(os.environ.get("QUANTLAB_FACTOR_GYM"))
    flag = bool(s.quantlab_factor_gym) if env_flag is None else env_flag
    allow = os.environ.get("QUANTLAB_FACTOR_GYM_TEST_ALLOWLIST")
    if allow is None:
        allow = s.quantlab_factor_gym_test_allowlist or ""
    token = os.environ.get("QUANTLAB_FACTOR_GYM_TEST_TOKEN")
    if token is None:
        token = s.quantlab_factor_gym_test_token or ""
    return flag, allow, token


def resolve_factor_gym_access(
    user: User,
    *,
    test_token: str | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Canonical access decision used by status + every /factor-gym/* mutating route."""
    flag, allow_raw, expected_token = _resolve_flag_sources(settings)

    if flag:
        return {
            "allowed": True,
            "enabled": True,
            "mode": "global",
            "test_entry": False,
            "label": "Factor Gym",
            "public_rollout": False,
            "denied_detail": None,
        }

    allow = parse_test_allowlist(allow_raw)
    identities = {
        (getattr(user, "email", None) or "").strip().lower(),
        (getattr(user, "username", None) or "").strip().lower(),
        str(getattr(user, "id", "")),
    }
    identities.discard("")
    if allow and (allow & identities):
        return {
            "allowed": True,
            "enabled": True,
            "mode": "allowlist",
            "test_entry": True,
            "label": "Factor Gym（测试版）",
            "public_rollout": False,
            "denied_detail": None,
        }

    expected = (expected_token or "").strip()
    provided = (test_token or "").strip()
    if expected and provided and secrets.compare_digest(provided, expected):
        return {
            "allowed": True,
            "enabled": True,
            "mode": "test_token",
            "test_entry": True,
            "label": "Factor Gym（测试版）",
            "public_rollout": False,
            "denied_detail": None,
        }

    return {
        "allowed": False,
        "enabled": False,
        "mode": "denied",
        "test_entry": False,
        "label": "Factor Gym",
        "public_rollout": False,
        "denied_detail": DENIED_DETAIL_INVITE_ONLY,
    }

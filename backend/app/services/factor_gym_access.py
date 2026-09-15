"""FACTOR_GYM_ACCESS_RESOLVER — single canonical gate for nav, page, and API.

Open Beta (Owner-approved):
  FACTOR_GYM_ACCESS_ALLOWED = authenticated AND NOT emergency_kill

QUANTLAB_FACTOR_GYM_OPEN_BETA=true (default) → all logged-in users.
QUANTLAB_FACTOR_GYM_KILL=true → emergency deny everyone (master kill).
QUANTLAB_FACTOR_GYM=true → legacy force-on (same Open Beta surface; not formal GA).

Allowlist / test token are internal QA only when Open Beta is off (not product path).

Frontend MUST gate on FACTOR_GYM_ACCESS_ALLOWED (alias ``allowed``), never on
``enabled`` alone. ``enabled`` / ``global_enabled`` remain the legacy flag only.
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from backend.app.core.config import Settings, get_settings
from backend.app.models.user import User

DENIED_DETAIL_LOGIN = "请先登录后使用 Factor Gym（测试版）。"
DENIED_DETAIL_KILLED = "Factor Gym（测试版）暂时关闭，请稍后再试。"
# Kept for tests / older clients; product copy no longer uses invite-only.
DENIED_DETAIL_INVITE_ONLY = DENIED_DETAIL_KILLED
DENIED_DETAIL_LEGACY = DENIED_DETAIL_KILLED

OPEN_BETA_LABEL = "Factor Gym（测试版）"


def parse_test_allowlist(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def _truthy_env(raw: str | None) -> bool | None:
    if raw is None:
        return None
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _resolve_flag_sources(settings: Settings | None) -> tuple[bool, bool, bool, str, str]:
    """Return (legacy_flag, open_beta, kill, allowlist_raw, token_raw)."""
    if settings is not None:
        return (
            bool(getattr(settings, "quantlab_factor_gym", False)),
            bool(getattr(settings, "quantlab_factor_gym_open_beta", True)),
            bool(getattr(settings, "quantlab_factor_gym_kill", False)),
            getattr(settings, "quantlab_factor_gym_test_allowlist", "") or "",
            getattr(settings, "quantlab_factor_gym_test_token", "") or "",
        )
    s = get_settings()
    env_flag = _truthy_env(os.environ.get("QUANTLAB_FACTOR_GYM"))
    flag = bool(s.quantlab_factor_gym) if env_flag is None else env_flag
    env_beta = _truthy_env(os.environ.get("QUANTLAB_FACTOR_GYM_OPEN_BETA"))
    open_beta = bool(s.quantlab_factor_gym_open_beta) if env_beta is None else env_beta
    env_kill = _truthy_env(os.environ.get("QUANTLAB_FACTOR_GYM_KILL"))
    kill = bool(s.quantlab_factor_gym_kill) if env_kill is None else env_kill
    allow = os.environ.get("QUANTLAB_FACTOR_GYM_TEST_ALLOWLIST")
    if allow is None:
        allow = s.quantlab_factor_gym_test_allowlist or ""
    token = os.environ.get("QUANTLAB_FACTOR_GYM_TEST_TOKEN")
    if token is None:
        token = s.quantlab_factor_gym_test_token or ""
    return flag, open_beta, kill, allow, token


def resolve_factor_gym_access(
    user: User | None,
    *,
    test_token: str | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Canonical access decision used by status + every /factor-gym/* route."""
    flag, open_beta, kill, allow_raw, expected_token = _resolve_flag_sources(settings)

    def _decision(
        *,
        access_allowed: bool,
        mode: str,
        test_entry: bool,
        label: str,
        denied_detail: str | None,
    ) -> dict[str, Any]:
        return {
            "FACTOR_GYM_ACCESS_ALLOWED": access_allowed,
            "allowed": access_allowed,
            "enabled": flag,
            "global_enabled": flag,
            "open_beta": open_beta and not kill,
            "mode": mode,
            "test_entry": test_entry,
            "label": label,
            "public_rollout": False,
            "denied_detail": denied_detail,
        }

    if kill:
        return _decision(
            access_allowed=False,
            mode="killed",
            test_entry=False,
            label=OPEN_BETA_LABEL,
            denied_detail=DENIED_DETAIL_KILLED,
        )

    authenticated = user is not None and bool(getattr(user, "id", None))

    # Open Beta or legacy force-on: any authenticated user.
    if (open_beta or flag) and authenticated:
        return _decision(
            access_allowed=True,
            mode="open_beta" if open_beta else "global",
            test_entry=True,
            label=OPEN_BETA_LABEL,
            denied_detail=None,
        )

    # Internal QA only when Open Beta is off (not a product dependency).
    if not open_beta and not flag:
        allow = parse_test_allowlist(allow_raw)
        identities: set[str] = set()
        if user is not None:
            identities = {
                (getattr(user, "email", None) or "").strip().lower(),
                (getattr(user, "username", None) or "").strip().lower(),
                str(getattr(user, "id", "")),
            }
            identities.discard("")
        if allow and (allow & identities):
            return _decision(
                access_allowed=True,
                mode="allowlist_qa",
                test_entry=True,
                label=OPEN_BETA_LABEL,
                denied_detail=None,
            )
        expected = (expected_token or "").strip()
        provided = (test_token or "").strip()
        if expected and provided and secrets.compare_digest(provided, expected):
            return _decision(
                access_allowed=True,
                mode="test_token_qa",
                test_entry=True,
                label=OPEN_BETA_LABEL,
                denied_detail=None,
            )

    if not authenticated:
        return _decision(
            access_allowed=False,
            mode="denied",
            test_entry=False,
            label=OPEN_BETA_LABEL,
            denied_detail=DENIED_DETAIL_LOGIN,
        )

    return _decision(
        access_allowed=False,
        mode="denied",
        test_entry=False,
        label=OPEN_BETA_LABEL,
        denied_detail=DENIED_DETAIL_KILLED,
    )

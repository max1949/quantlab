"""Version semantics — what bumps a strategy version (QLN-1)."""

from __future__ import annotations

import re
from enum import Enum


class ChangeClass(str, Enum):
    """Aligned with Constitution parameter classes (subset for domain)."""

    A_DISPLAY = "A_DISPLAY"
    B_BEHAVIOR = "B_BEHAVIOR"
    C_RISK_CRITICAL = "C_RISK_CRITICAL"
    D_BROKER_EXEC_SECRET = "D_BROKER_EXEC_SECRET"


class VersionBump(str, Enum):
    NONE = "NONE"
    PATCH = "PATCH"
    MINOR = "MINOR"
    MAJOR = "MAJOR"


_VERSION_RE = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$", re.I)


def classify_strategy_change(
    *,
    changes_trading_behavior: bool,
    changes_risk_limits: bool,
    changes_broker_or_secret: bool,
    display_only: bool,
) -> tuple[ChangeClass, VersionBump]:
    if changes_broker_or_secret:
        return ChangeClass.D_BROKER_EXEC_SECRET, VersionBump.MAJOR
    if changes_risk_limits:
        return ChangeClass.C_RISK_CRITICAL, VersionBump.MAJOR
    if changes_trading_behavior:
        return ChangeClass.B_BEHAVIOR, VersionBump.MINOR
    if display_only:
        return ChangeClass.A_DISPLAY, VersionBump.NONE
    return ChangeClass.B_BEHAVIOR, VersionBump.MINOR


def next_strategy_version(current: str, bump: VersionBump) -> str:
    if bump == VersionBump.NONE:
        return current if current.startswith("v") else f"v{current}" if current[0].isdigit() else current
    m = _VERSION_RE.match((current or "v0").strip())
    if not m:
        # Opaque versions (e.g. "v1") → append suffix for behavior bumps.
        base = current or "v0"
        if bump == VersionBump.PATCH:
            return f"{base}.1"
        if bump == VersionBump.MINOR:
            return f"{base}.1"
        return f"{base}+major"
    major = int(m.group(1))
    minor = int(m.group(2) or 0)
    patch = int(m.group(3) or 0)
    if bump == VersionBump.MAJOR:
        major, minor, patch = major + 1, 0, 0
    elif bump == VersionBump.MINOR:
        minor, patch = minor + 1, 0
    else:
        patch += 1
    if m.group(3) is not None or bump == VersionBump.PATCH:
        return f"v{major}.{minor}.{patch}"
    if m.group(2) is not None or bump == VersionBump.MINOR:
        return f"v{major}.{minor}"
    return f"v{major}"

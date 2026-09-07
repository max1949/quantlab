"""Time governance policy for experiments (QLN-3)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from engine.experiment.errors import ExperimentError

BarBoundary = Literal["left_open_right_closed", "left_closed_right_open"]


class TimeGovernance(BaseModel):
    """Canonical time rules frozen into every experiment record."""

    timezone: str = "UTC"
    calendar: str | None = None
    session: str | None = None
    bar_boundary: BarBoundary = "left_open_right_closed"
    require_tz_aware: bool = True
    require_monotonic_increasing: bool = True
    forbid_duplicate_timestamps: bool = True
    dst_policy: str = "store_and_compute_in_UTC"
    schema_version: str = "1.0"

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def validate_time_governance(tg: TimeGovernance | dict[str, Any]) -> TimeGovernance:
    if isinstance(tg, dict):
        try:
            tg = TimeGovernance.model_validate(tg)
        except Exception as exc:  # noqa: BLE001
            raise ExperimentError(f"invalid time governance: {exc}") from exc
    if tg.timezone.upper() != "UTC" and tg.dst_policy == "ignore_dst":
        raise ExperimentError("DST ignore policy forbidden; use UTC storage")
    return tg


def assert_frame_time_governance(index_info: dict[str, Any], tg: TimeGovernance) -> None:
    """Fail closed when frame violates frozen time governance."""
    if tg.require_tz_aware and not index_info.get("tz_aware"):
        raise ExperimentError("time governance: timestamps must be tz-aware")
    if tg.require_monotonic_increasing and not index_info.get("monotonic"):
        raise ExperimentError("time governance: timestamps must be monotonic increasing")
    if tg.forbid_duplicate_timestamps and int(index_info.get("duplicates", 0)) > 0:
        raise ExperimentError("time governance: duplicate timestamps forbidden")

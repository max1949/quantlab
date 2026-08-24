"""Realtime data freshness policy (centralized thresholds)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RealtimeDataPolicy:
    """Stale-data protection thresholds for paper sandbox."""

    max_event_age_seconds: float = 30.0
    max_stream_gap_seconds: float = 60.0
    warn_event_age_seconds: float = 10.0
    duplicate_window_seconds: float = 1.0

    def is_stale(self, event_age_seconds: float) -> bool:
        return event_age_seconds > self.max_event_age_seconds

    def is_warn(self, event_age_seconds: float) -> bool:
        return event_age_seconds > self.warn_event_age_seconds

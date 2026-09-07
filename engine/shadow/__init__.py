"""QLN-8 Shadow Twin / Flight Recorder package."""

from __future__ import annotations

from engine.shadow.flight_recorder import FlightEvent, FlightRecorder
from engine.shadow.replay import behavior_parity_report, loss_attribution, replay_events
from engine.shadow.twin import DivergenceEvent, ShadowSnapshot, compare_twins

__all__ = [
    "DivergenceEvent",
    "FlightEvent",
    "FlightRecorder",
    "ShadowSnapshot",
    "behavior_parity_report",
    "compare_twins",
    "loss_attribution",
    "replay_events",
]

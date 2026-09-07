"""Replay engine + loss attribution (QLN-8)."""

from __future__ import annotations

from typing import Any

from engine.shadow.flight_recorder import FlightEvent, FlightRecorder


def replay_events(
    recorder: FlightRecorder,
    *,
    strategy_id: str,
) -> list[dict[str, Any]]:
    """Deterministic replay of recorded events for a strategy."""
    return [e.model_dump(mode="json") for e in recorder.list_events(strategy_id=strategy_id)]


def loss_attribution(events: list[FlightEvent]) -> dict[str, Any]:
    """Attribute losses from OUTCOME events (research-grade)."""
    losses: list[dict[str, Any]] = []
    total = 0.0
    for ev in events:
        if ev.event_type != "OUTCOME":
            continue
        pnl = float(ev.happened.get("pnl") or 0.0)
        if pnl < 0:
            losses.append(
                {
                    "event_id": ev.event_id,
                    "pnl": pnl,
                    "why": ev.why,
                    "risk": ev.risk,
                }
            )
            total += pnl
    return {"loss_events": losses, "total_loss": total, "n_loss_events": len(losses)}


def behavior_parity_report(
    *,
    reference_actions: list[str],
    shadow_actions: list[str],
) -> dict[str, Any]:
    n = max(len(reference_actions), len(shadow_actions))
    mismatches = []
    for i in range(n):
        a = reference_actions[i] if i < len(reference_actions) else None
        b = shadow_actions[i] if i < len(shadow_actions) else None
        if a != b:
            mismatches.append({"i": i, "reference": a, "shadow": b})
    return {
        "parity": "PASS" if not mismatches else "FAIL",
        "mismatches": mismatches,
        "n_compared": n,
    }

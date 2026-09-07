"""Flight Recorder — append-only event journal for what/why/risk/outcome."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "OBSERVATION",
    "DECISION",
    "RISK_ADJUDICATION",
    "EXECUTION",
    "INTERVENTION",
    "OUTCOME",
]


class FlightEvent(BaseModel):
    event_id: str
    ts: str
    strategy_id: str
    event_type: EventType
    saw: dict[str, Any] = Field(default_factory=dict)  # what was seen
    why: str = ""  # why decision
    risk: dict[str, Any] = Field(default_factory=dict)  # risk adjudication
    happened: dict[str, Any] = Field(default_factory=dict)  # what occurred
    meta: dict[str, Any] = Field(default_factory=dict)


class FlightRecorder:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path or Path("data") / "flight_recorder" / "events.jsonl")

    def ensure(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append(self, event: FlightEvent) -> None:
        self.ensure()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")

    def list_events(self, *, strategy_id: str | None = None) -> list[FlightEvent]:
        if not self.path.exists():
            return []
        out: list[FlightEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = FlightEvent.model_validate(json.loads(line))
            if strategy_id is None or ev.strategy_id == strategy_id:
                out.append(ev)
        return out

    def explain_event(self, event_id: str) -> dict[str, Any] | None:
        """Acceptance: answer what/why/risk/what-happened for a selected event."""
        for ev in self.list_events():
            if ev.event_id == event_id:
                return {
                    "event_id": ev.event_id,
                    "saw": ev.saw,
                    "why": ev.why,
                    "risk": ev.risk,
                    "happened": ev.happened,
                    "event_type": ev.event_type,
                    "strategy_id": ev.strategy_id,
                    "ts": ev.ts,
                }
        return None

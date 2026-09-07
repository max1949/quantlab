"""Graveyard index — QLN-6 view over rejects / KILL outcomes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from engine.validation.graveyard import append_reject


class GraveyardIndex(BaseModel):
    entries: list[dict[str, Any]] = Field(default_factory=list)

    def add(self, entry: dict[str, Any]) -> None:
        self.entries.append(dict(entry))

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def index_reject(
    *,
    strategy_id: str,
    version: str,
    reason: str,
    gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "strategy_id": strategy_id,
        "version": version,
        "reason": reason,
        "gates": gates or {},
        "status": "KILLED_OR_REJECTED",
    }


def persist_reject(
    *,
    strategy_id: str,
    version: str,
    reason: str,
    gates: dict[str, Any] | None = None,
    market: str = "",
    timeframe: str = "1d",
    hypothesis: str = "",
    path: Path | str | None = None,
) -> Path:
    """Dual-write into validation graveyard JSONL (append-only SSOT)."""
    payload = {
        "strategy_id": strategy_id,
        "strategy_version": version,
        "hypothesis": hypothesis or reason,
        "market": market,
        "timeframe": timeframe,
        "validation_results": {"gates": gates or {}, "qln6": True},
        "failure_reason": reason,
    }
    return append_reject(payload, path=Path(path) if path else None)


def load_legacy_graveyard(path: Path | str | None = None) -> list[dict[str, Any]]:
    p = Path(path or Path("data") / "strategy_graveyard" / "rejects.jsonl")
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows

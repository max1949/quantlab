"""Graveyard index — QLN-6 view over rejects / KILL outcomes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


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


def load_legacy_graveyard(path: Path | str | None = None) -> list[dict[str, Any]]:
    p = Path(path or Path("data") / "strategy_graveyard" / "rejects.jsonl")
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows

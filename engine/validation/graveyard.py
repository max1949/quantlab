"""Strategy Graveyard — append-only reject archive (anti-repeat learning)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_GRAVEYARD = Path("data/strategy_graveyard/rejects.jsonl")


@dataclass
class GraveyardEntry:
    strategy_id: str
    strategy_version: str
    hypothesis: str
    market: str
    timeframe: str
    validation_results: dict[str, Any]
    failure_reason: str
    rejected_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_reject(
    entry: GraveyardEntry | dict[str, Any],
    *,
    path: Path | None = None,
) -> Path:
    target = path or DEFAULT_GRAVEYARD
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = entry.to_dict() if isinstance(entry, GraveyardEntry) else dict(entry)
    payload.setdefault("rejected_at", _now())
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return target


def list_rejects(*, path: Path | None = None) -> list[dict[str, Any]]:
    target = path or DEFAULT_GRAVEYARD
    if not target.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def fingerprint_seen(
    strategy_id: str,
    hypothesis: str,
    *,
    path: Path | None = None,
) -> bool:
    """True if a near-duplicate reject already exists (id or hypothesis)."""
    hid = hypothesis.strip().lower()
    for row in list_rejects(path=path):
        if row.get("strategy_id") == strategy_id:
            return True
        if str(row.get("hypothesis") or "").strip().lower() == hid:
            return True
    return False

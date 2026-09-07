"""Research Memory — store positive and negative results (NO_EDGE_FOUND allowed)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


Outcome = Literal["PROMOTE", "HOLD", "KILL", "NO_EDGE_FOUND", "INSUFFICIENT"]


class MemoryRecord(BaseModel):
    strategy_id: str
    version: str
    outcome: Outcome
    reasons: list[str] = Field(default_factory=list)
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    dataset_id: str = ""
    negative_result: bool = False


class ResearchMemory:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path or Path("data") / "research_memory" / "memory.jsonl")

    def ensure(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append(self, record: MemoryRecord) -> None:
        self.ensure()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) + "\n")

    def list_records(self) -> list[MemoryRecord]:
        if not self.path.exists():
            return []
        out: list[MemoryRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(MemoryRecord.model_validate(json.loads(line)))
        return out

    def negative_results(self) -> list[MemoryRecord]:
        return [r for r in self.list_records() if r.negative_result or r.outcome in ("KILL", "NO_EDGE_FOUND")]

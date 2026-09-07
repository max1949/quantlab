"""Append-only Experiment Ledger (filesystem JSONL) — immutable records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from engine.experiment.errors import ExperimentError
from engine.experiment.record import ExperimentRecord

DEFAULT_LEDGER_REL = Path("data") / "experiment_ledger" / "experiments.jsonl"


def default_ledger_path(root: Path | None = None) -> Path:
    base = root or Path.cwd()
    return (base / DEFAULT_LEDGER_REL).resolve()


class ExperimentLedger:
    """Append-only store. Updates are forbidden; use a new experiment_id."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else default_ledger_path()

    def ensure(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append(self, record: ExperimentRecord) -> ExperimentRecord:
        if not record.sealed:
            raise ExperimentError("only sealed experiments may enter the ledger")
        # Verify content hash integrity
        expected = record.compute_content_hash()
        if record.content_hash != expected:
            raise ExperimentError("experiment content_hash mismatch before append")
        # Reject mutation of existing id
        existing = self.get(record.experiment_id)
        if existing is not None:
            raise ExperimentError(
                f"immutable ledger: experiment_id already exists: {record.experiment_id}"
            )
        self.ensure()
        line = json.dumps(record.canonical_dict(), ensure_ascii=False, sort_keys=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return record

    def iter_records(self) -> Iterator[ExperimentRecord]:
        if not self.path.exists():
            return
            yield  # pragma: no cover
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                yield ExperimentRecord.model_validate(json.loads(line))

    def get(self, experiment_id: str) -> ExperimentRecord | None:
        for rec in self.iter_records():
            if rec.experiment_id == experiment_id:
                return rec
        return None

    def list_ids(self) -> list[str]:
        return [r.experiment_id for r in self.iter_records()]

    def verify_integrity(self) -> list[str]:
        """Return list of integrity problems (empty = OK)."""
        problems: list[str] = []
        seen: set[str] = set()
        for rec in self.iter_records():
            if rec.experiment_id in seen:
                problems.append(f"duplicate_id:{rec.experiment_id}")
            seen.add(rec.experiment_id)
            if rec.content_hash != rec.compute_content_hash():
                problems.append(f"hash_mismatch:{rec.experiment_id}")
            if not rec.sealed:
                problems.append(f"unsealed:{rec.experiment_id}")
        return problems

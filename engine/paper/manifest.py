"""Run manifest for PaperRun reproducibility."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(data).encode()).hexdigest()


@dataclass
class RunManifest:
    strategy_spec_id: str
    strategy_spec_version: str
    strategy_spec_hash: str
    compiled_strategy_hash: str
    nautilus_version: str
    data_provider: str
    instrument: str
    venue: str
    risk_policy_hash: str
    application_commit: str
    environment: str
    started_at: str
    engine: str = "NAUTILUS_SANDBOX"
    engine_version: str = "1.231.0"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def manifest_hash(self) -> str:
        return content_hash(self.to_dict())


def build_run_manifest(
    *,
    strategy_spec_id: str,
    strategy_spec_version: str,
    strategy_spec_hash: str,
    compiled_strategy_hash: str,
    data_provider: str,
    instrument: str,
    venue: str,
    risk_policy_hash: str,
    application_commit: str,
    environment: str,
    nautilus_version: str = "1.231.0",
    extra: dict[str, Any] | None = None,
) -> RunManifest:
    return RunManifest(
        strategy_spec_id=strategy_spec_id,
        strategy_spec_version=strategy_spec_version,
        strategy_spec_hash=strategy_spec_hash,
        compiled_strategy_hash=compiled_strategy_hash,
        nautilus_version=nautilus_version,
        data_provider=data_provider,
        instrument=instrument,
        venue=venue,
        risk_policy_hash=risk_policy_hash,
        application_commit=application_commit,
        environment=environment,
        started_at=datetime.now(timezone.utc).isoformat(),
        extra=extra or {},
    )

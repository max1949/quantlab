"""Audit event domain schema (QLN-1) — contract only, not a full audit platform."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    TRANSITION = "TRANSITION"
    PROMOTE = "PROMOTE"
    HOLD = "HOLD"
    KILL = "KILL"
    START = "START"
    STOP = "STOP"
    DENY = "DENY"
    OWNER_DECISION = "OWNER_DECISION"
    RISK_DECISION = "RISK_DECISION"
    SYSTEM = "SYSTEM"


@dataclass(slots=True)
class AuditEvent:
    action: AuditAction
    target_kind: str
    target_id: str
    actor: str = "system"
    previous_state: str | None = None
    new_state: str | None = None
    reason: str = ""
    timestamp_utc: str = ""
    environment: str | None = None
    source: str = "quantlab.domain"
    correlation_id: str | None = None
    run_id: str | None = None
    evidence_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp_utc:
            self.timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Secrets must never appear in metadata.
        banned = ("secret", "token", "password", "api_key", "private_key")
        for key in list(self.metadata.keys()):
            lk = key.lower()
            if any(b in lk for b in banned):
                raise ValueError(f"audit metadata must not contain secret key: {key}")


def audit_event_to_dict(event: AuditEvent) -> dict[str, Any]:
    payload = asdict(event)
    payload["action"] = event.action.value
    return payload

"""Immutable domain identifiers (QLN-1). Display names are never identity."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum


class DomainEntityKind(str, Enum):
    STRATEGY = "strategy"
    STRATEGY_VERSION = "strategy_version"
    EXPERIMENT = "experiment"
    EVIDENCE = "evidence"
    RUN = "run"
    DATASET = "dataset"
    ARTIFACT = "artifact"
    ENVIRONMENT = "environment"
    ENGINE = "engine"
    EXECUTION_SESSION = "execution_session"


_KIND_PREFIX = {
    DomainEntityKind.STRATEGY: "str",
    DomainEntityKind.STRATEGY_VERSION: "stv",
    DomainEntityKind.EXPERIMENT: "exp",
    DomainEntityKind.EVIDENCE: "evd",
    DomainEntityKind.RUN: "run",
    DomainEntityKind.DATASET: "dst",
    DomainEntityKind.ARTIFACT: "art",
    DomainEntityKind.ENVIRONMENT: "env",
    DomainEntityKind.ENGINE: "eng",
    DomainEntityKind.EXECUTION_SESSION: "exs",
}

_ID_RE = re.compile(r"^ql_(?P<prefix>[a-z]{3})_(?P<body>[0-9a-f]{32})$")


@dataclass(frozen=True, slots=True)
class DomainId:
    """Immutable public domain identity. Rename of display labels must not change this."""

    kind: DomainEntityKind
    value: str

    def __post_init__(self) -> None:
        m = _ID_RE.match(self.value)
        if not m:
            raise ValueError(f"invalid domain id: {self.value!r}")
        prefix = m.group("prefix")
        expected = _KIND_PREFIX[self.kind]
        if prefix != expected:
            raise ValueError(
                f"kind mismatch: declared={self.kind.value} prefix={prefix} expected={expected}"
            )

    @property
    def prefix(self) -> str:
        return _KIND_PREFIX[self.kind]


def new_domain_id(kind: DomainEntityKind, *, seed: str | None = None) -> DomainId:
    """Create a new immutable domain id. Optional seed yields deterministic ids for tests."""
    prefix = _KIND_PREFIX[kind]
    if seed is None:
        body = uuid.uuid4().hex
    else:
        body = uuid.uuid5(uuid.NAMESPACE_URL, f"quantlab:{kind.value}:{seed}").hex
    return DomainId(kind=kind, value=f"ql_{prefix}_{body}")


def parse_domain_id(raw: str) -> DomainId:
    text = (raw or "").strip()
    m = _ID_RE.match(text)
    if not m:
        raise ValueError(f"invalid domain id: {raw!r}")
    prefix = m.group("prefix")
    kind = next((k for k, p in _KIND_PREFIX.items() if p == prefix), None)
    if kind is None:
        raise ValueError(f"unknown domain id prefix: {prefix}")
    return DomainId(kind=kind, value=text)


def db_pk_is_not_domain_id() -> bool:
    """Documented rule: SQL UUID PK ≠ public DomainId; both may coexist via mapping table later."""
    return True

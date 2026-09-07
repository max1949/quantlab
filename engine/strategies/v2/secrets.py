"""Secret scanning for Strategy Packages — PACKAGE_SECRET_COUNT must be 0."""

from __future__ import annotations

import re
from typing import Any

# Keys that look like credential carriers (avoid matching policy flags like secrets_forbidden)
_SECRET_KEY_RE = re.compile(
    r"^(.+_)?(api[_-]?key|secret|password|passwd|token|credential|access[_-]?key|"
    r"private[_-]?key|broker[_-]?key|openai|anthropic|database[_-]?url|dsn|"
    r"authorization|bearer|env[_-]?secret)$"
    r"|.*(api[_-]?key|password|passwd|access[_-]?token|private[_-]?key|"
    r"broker[_-]?api|client[_-]?secret|db[_-]?password|openai[_-]?api|"
    r"anthropic[_-]?api|database[_-]?url|ai[_-]?key).*",
    re.IGNORECASE,
)

_SECRET_VALUE_RE = re.compile(
    r"(sk-[a-zA-Z0-9]{20,}|Bearer\s+[A-Za-z0-9\-._~+/]+=*|"
    r"AKIA[0-9A-Z]{16}|postgres://\S+|mysql://\S+|"
    r"mongodb(\+srv)?://\S+)",
    re.IGNORECASE,
)


def _walk(obj: Any, path: str = "") -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            if _SECRET_KEY_RE.search(str(k)):
                hits.append((p, f"secret_key:{k}"))
            hits.extend(_walk(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_walk(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if _SECRET_VALUE_RE.search(obj):
            hits.append((path, "secret_value_pattern"))
    return hits


def find_secrets(payload: Any) -> list[tuple[str, str]]:
    return _walk(payload)


def assert_no_secrets(payload: Any) -> None:
    from engine.strategies.v2.errors import SpecV2Error

    hits = find_secrets(payload)
    if hits:
        raise SpecV2Error(
            f"PACKAGE_SECRET_COUNT={len(hits)}; secrets must not enter Strategy Package: "
            + ", ".join(f"{p}" for p, _ in hits[:8])
        )

"""Deterministic hash policy primitives (QLN-1). Not a full Experiment Ledger."""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any


class HashKind(str, Enum):
    STRATEGY_DEFINITION = "strategy_definition"
    CONFIG = "config"
    DATASET = "dataset"
    ARTIFACT = "artifact"
    ENGINE_FINGERPRINT = "engine_fingerprint"


# Fields that must never enter exportable hash payloads.
_SECRET_KEY_FRAGMENTS = (
    "secret",
    "password",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
    "authorization",
)


def _is_secret_key(key: str) -> bool:
    k = key.lower().replace("-", "_")
    return any(frag in k for frag in _SECRET_KEY_FRAGMENTS)


def _strip_secrets(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if _is_secret_key(str(key)):
                continue
            out[str(key)] = _strip_secrets(value)
        return out
    if isinstance(obj, list):
        return [_strip_secrets(x) for x in obj]
    return obj


# Metadata that must not silently drift content hashes.
_EXCLUDED_META = frozenset(
    {
        "created_at",
        "updated_at",
        "timestamp",
        "ts",
        "wall_time",
        "display_name",
        "name_zh",
        "label",
        "ui_label",
    }
)


def _strip_meta(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            str(k): _strip_meta(v)
            for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))
            if str(k) not in _EXCLUDED_META and not _is_secret_key(str(k))
        }
    if isinstance(obj, list):
        return [_strip_meta(x) for x in obj]
    return obj


def canonical_json_bytes(payload: Any) -> bytes:
    cleaned = _strip_meta(_strip_secrets(payload))
    return json.dumps(
        cleaned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def compute_hash(kind: HashKind, payload: Any) -> str:
    digest = hashlib.sha256()
    digest.update(kind.value.encode("utf-8"))
    digest.update(b"|")
    digest.update(canonical_json_bytes(payload))
    return digest.hexdigest()


def hash_strategy_definition(definition: dict[str, Any]) -> str:
    return compute_hash(HashKind.STRATEGY_DEFINITION, definition)


def hash_config(config: dict[str, Any]) -> str:
    return compute_hash(HashKind.CONFIG, config)


def hash_dataset_payload(payload: dict[str, Any]) -> str:
    return compute_hash(HashKind.DATASET, payload)


def fingerprint_engine(
    *,
    engine_name: str,
    engine_version: str,
    adapter_version: str,
) -> str:
    return compute_hash(
        HashKind.ENGINE_FINGERPRINT,
        {
            "engine_name": engine_name,
            "engine_version": engine_version,
            "adapter_version": adapter_version,
        },
    )

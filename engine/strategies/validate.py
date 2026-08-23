"""Validate and load Strategy Specifications from dict/YAML/JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.strategies.spec import StrategySpec

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML may be absent on minimal envs
    yaml = None  # type: ignore[assignment]


class SpecValidationError(ValueError):
    pass


def validate_spec(data: dict[str, Any]) -> StrategySpec:
    try:
        spec = StrategySpec.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        raise SpecValidationError(str(exc)) from exc
    _semantic_checks(spec)
    return spec


def _semantic_checks(spec: StrategySpec) -> None:
    if not spec.strategy.id.strip():
        raise SpecValidationError("strategy.id required")
    if not spec.strategy.version.strip():
        raise SpecValidationError("strategy.version required")
    if not spec.market.instrument.strip():
        raise SpecValidationError("market.instrument required")
    if spec.strategy.status == "LIVE" and "LIVE" not in spec.deployment.permitted_environments:
        raise SpecValidationError("LIVE status requires LIVE in permitted_environments")
    if spec.strategy.ambiguous and spec.strategy.deployable:
        raise SpecValidationError("ambiguous specs cannot be deployable")
    if "LIVE" in spec.deployment.permitted_environments and not spec.strategy.user_approved:
        # Hard AI safety: never mark LIVE-capable without human approval flag
        raise SpecValidationError("LIVE environment requires user_approved=true")


def load_spec(path: str | Path) -> StrategySpec:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise SpecValidationError("PyYAML required to load YAML strategy specs")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise SpecValidationError("spec root must be a mapping")
    return validate_spec(data)


def dump_spec(spec: StrategySpec, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise SpecValidationError("PyYAML required to dump YAML strategy specs")
        p.write_text(yaml.safe_dump(spec.canonical_dict(), sort_keys=False, allow_unicode=True), encoding="utf-8")
    else:
        p.write_text(json.dumps(spec.canonical_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return p

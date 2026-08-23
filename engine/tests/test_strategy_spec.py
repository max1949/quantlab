"""Phase 2: Strategy Spec schema, versioning, compiler determinism."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.strategies import (
    SpecValidationError,
    compile_deterministic,
    compile_spec,
    load_spec,
    validate_spec,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_JSON = ROOT / "strategy_specs" / "examples" / "golden_01_ema_trend.v1.json"
EXAMPLE_YAML = ROOT / "strategy_specs" / "examples" / "golden_01_ema_trend.v1.yaml"


def test_spec_schema_from_json():
    data = json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))
    spec = validate_spec(data)
    assert spec.strategy.id == "golden_01_ema_trend"
    assert spec.strategy.version == "v1"
    assert spec.deployment.permitted_environments == ["BACKTEST"]


def test_spec_yaml_load_when_available():
    pytest.importorskip("yaml")
    spec = load_spec(EXAMPLE_YAML)
    assert spec.market.instrument == "EUR/USD"


def test_spec_versioning_preserves_parent():
    data = json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))
    spec = validate_spec(data)
    v2 = spec.bump_version("v2", change_reason="tune slow ema", created_by="phase2")
    assert v2.strategy.version == "v2"
    assert v2.strategy.parent_version == "v1"
    assert v2.strategy.status == "DRAFT"
    assert v2.strategy.user_approved is False
    assert v2.content_hash() != spec.content_hash()


def test_ambiguous_not_deployable():
    data = json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))
    data["strategy"]["ambiguous"] = True
    data["strategy"]["deployable"] = True
    with pytest.raises(SpecValidationError):
        validate_spec(data)


def test_live_requires_user_approval():
    data = json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))
    data["deployment"]["permitted_environments"] = ["BACKTEST", "LIVE"]
    data["strategy"]["user_approved"] = False
    with pytest.raises(SpecValidationError):
        validate_spec(data)


def test_compiler_determinism():
    data = json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))
    a = compile_deterministic(data)
    b = compile_deterministic(data)
    assert a == b
    assert a["kind"] == "SPEC_COMPILED_STRATEGY"
    assert a["template"] == "ema_cross"
    assert a["nautilus_params"]["fast_ema"] == 10
    assert a["nautilus_params"]["slow_ema"] == 20


def test_compiler_rejects_ambiguous():
    data = json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))
    data["strategy"]["ambiguous"] = True
    data["strategy"]["deployable"] = False
    with pytest.raises(SpecValidationError):
        compile_spec(data)

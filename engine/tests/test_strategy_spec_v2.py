"""QLN-2 Strategy Spec v2 / Contract / Package acceptance tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from engine.strategies.compiler import compile_deterministic
from engine.strategies.v2 import (
    CodeEscapeHatch,
    CustomComponentDecl,
    compile_spec_v2_deterministic,
    derive_child_lineage,
    export_package,
    import_package,
    migrate_v1_file_to_v2,
    migrate_v1_to_v2,
    package_contains_secrets,
    semantic_diff,
    validate_contract,
    validate_escape_hatch,
    validate_invariants,
    validate_spec_v2,
)
from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.migrate import assert_semantic_drift_zero
from engine.strategies.v2.package import build_package
from engine.strategies.v2.secrets import find_secrets
from engine.strategies.validate import load_spec

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_FX = ROOT / "strategy_specs" / "examples" / "golden_01_ema_trend.v1.yaml"
GOLDEN_BTC = ROOT / "strategy_specs" / "examples" / "golden_btc_ema_trend.v1.yaml"


@pytest.fixture(params=[GOLDEN_FX, GOLDEN_BTC])
def golden_path(request):
    return request.param


def test_v1_to_v2_migration_semantic_drift_zero(golden_path):
    v1 = load_spec(golden_path)
    v2, contract, inv = migrate_v1_to_v2(v1)
    assert_semantic_drift_zero(v1, v2)
    validate_contract(contract)
    validate_invariants(inv)
    assert v2.identity.schema_version == "2.0"
    assert v2.parameters.values.get("ema_fast") == 10
    assert v2.parameters.values.get("ema_slow") == 20


def test_v1_v2_adapter_params_parity(golden_path):
    v1 = load_spec(golden_path)
    v2, _, _ = migrate_v1_to_v2(v1)
    c1 = compile_deterministic(v1)
    c2 = compile_spec_v2_deterministic(v2)
    assert c1["nautilus_params"] == c2["nautilus_params"]
    assert c1["template"] == c2["template"] == "ema_cross"
    assert c2["generator_version"] == "spec_compiler_v2"
    # Determinism: same input → same output
    assert c2 == compile_spec_v2_deterministic(v2)


def test_package_export_import_hash(tmp_path, golden_path):
    v2, contract, inv = migrate_v1_file_to_v2(golden_path)
    lineage = derive_child_lineage(v2, v2)  # self as baseline lineage shape
    # For baseline package use lineage_from parent fields without forcing child kind noise
    from engine.strategies.v2.lineage import lineage_from_spec

    lineage = lineage_from_spec(v2)
    pkg = build_package(spec=v2, contract=contract, invariants=inv, lineage=lineage)
    assert package_contains_secrets(pkg) == 0
    out = tmp_path / "pkg.json"
    export_package(pkg, out)
    loaded = import_package(out)
    assert loaded.compute_hash() == pkg.compute_hash()
    assert loaded.strategy_spec.identity.strategy_id == v2.identity.strategy_id
    assert loaded.parameters["ema_fast"] == 10


def test_package_secret_rejection():
    v2, contract, inv = migrate_v1_file_to_v2(GOLDEN_FX)
    dirty = build_package(spec=v2, contract=contract, invariants=inv)
    export = dirty.to_export_dict()
    export["strategy_spec"]["metadata"]["broker_api_key"] = "sk-live-secret-should-not-pass-1234567890"
    assert len(find_secrets(export)) >= 1
    with pytest.raises(SpecV2Error):
        from engine.strategies.v2.secrets import assert_no_secrets

        assert_no_secrets(export)


def test_package_secret_patterns():
    payloads = [
        {"openai_api_key": "x"},
        {"db_password": "p"},
        {"access_token": "t"},
        {"authorization": "Bearer abc"},
        {"note": "postgres://user:pass@host/db"},
        {"env_secret": "z"},
        {"ai_key": "sk-abcdefghijklmnopqrstuvwxyz012345"},
    ]
    for p in payloads:
        assert find_secrets(p), p


def test_hash_mismatch_fail_closed(tmp_path):
    v2, contract, inv = migrate_v1_file_to_v2(GOLDEN_FX)
    pkg = build_package(spec=v2, contract=contract, invariants=inv)
    out = tmp_path / "pkg.json"
    export_package(pkg, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    data["manifest"]["content_hash"] = "0" * 64
    out.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SpecV2Error, match="hash mismatch"):
        import_package(out)


def test_semantic_diff_classes():
    v2, _, _ = migrate_v1_file_to_v2(GOLDEN_FX)
    other = validate_spec_v2(copy.deepcopy(v2.canonical_dict()))
    other.metadata.description = "changed prose only"
    d_meta = semantic_diff(v2, other)
    assert "metadata_only" in d_meta.summary_classes
    assert d_meta.is_breaking is False

    other2 = validate_spec_v2(copy.deepcopy(v2.canonical_dict()))
    other2.parameters.values["ema_fast"] = 12
    # also mirror into condition for realism
    other2.signal_logic.entry_long[0].params["fast"] = 12
    d_param = semantic_diff(v2, other2)
    assert "parameter" in d_param.summary_classes or "logic" in d_param.summary_classes

    other3 = validate_spec_v2(copy.deepcopy(v2.canonical_dict()))
    other3.risk.max_drawdown = 0.5
    d_risk = semantic_diff(v2, other3)
    assert "risk" in d_risk.summary_classes
    assert d_risk.is_breaking is True


def test_lineage_parameter_vs_logic_child():
    parent, _, _ = migrate_v1_file_to_v2(GOLDEN_FX)
    child_p = validate_spec_v2(copy.deepcopy(parent.canonical_dict()))
    child_p.identity.version = "v1.1"
    child_p.identity.parent_version = parent.identity.version
    child_p.parameters.values["ema_fast"] = 12
    # Keep signal params in sync for package consistency but classify via diff
    lin = derive_child_lineage(parent, child_p)
    assert lin.parent_version == parent.identity.version
    assert lin.child_kind in ("parameter_only_child", "logic_changing_child")

    child_l = validate_spec_v2(copy.deepcopy(parent.canonical_dict()))
    child_l.identity.version = "v2"
    child_l.signal_logic.entry_long = []
    lin2 = derive_child_lineage(parent, child_l)
    assert lin2.child_kind == "logic_changing_child"


def test_escape_hatch_contract():
    hatch = validate_escape_hatch(
        CodeEscapeHatch(
            enabled=True,
            components=[
                CustomComponentDecl(
                    name="custom_filter",
                    language="python",
                    entrypoint="pkg.mod:Filter",
                    content_hash="a" * 32,
                    capabilities=["filter"],
                )
            ],
        )
    )
    assert hatch.must_respect_contract is True
    with pytest.raises(SpecV2Error):
        validate_escape_hatch(
            CodeEscapeHatch(enabled=True, must_respect_invariants=False, components=[])
        )
    with pytest.raises(SpecV2Error):
        validate_escape_hatch(
            {
                "enabled": True,
                "components": [
                    {
                        "name": "bad",
                        "language": "python",
                        "entrypoint": "x:y",
                        "content_hash": "short",
                        "capabilities": ["not_a_cap"],
                    }
                ],
            }
        )


def test_invalid_spec_fail_closed():
    v2, _, _ = migrate_v1_file_to_v2(GOLDEN_FX)
    bad = v2.canonical_dict()
    bad["identity"]["strategy_id"] = ""
    with pytest.raises(SpecV2Error):
        validate_spec_v2(bad)

    bad2 = v2.canonical_dict()
    bad2["risk"]["max_drawdown"] = 2.0
    with pytest.raises(SpecV2Error):
        validate_spec_v2(bad2)

    bad3 = v2.canonical_dict()
    bad3["compatibility"]["permitted_environments"] = ["LIVE"]
    bad3["metadata"]["user_approved"] = False
    with pytest.raises(SpecV2Error):
        validate_spec_v2(bad3)

    with pytest.raises(SpecV2Error):
        validate_contract(
            {
                "contract_id": "c",
                "strategy_id": "s",
                "version": "v1",
                "what": "w",
                "why": "y",
                "risk": "r",
                "when": [],
                "when_not": ["x"],
                "invalidation": ["i"],
            }
        )

    with pytest.raises(SpecV2Error):
        validate_invariants({"strategy_id": "s", "version": "v1", "rules": []})


def test_invariant_max_leverage_violation():
    v2, contract, inv = migrate_v1_file_to_v2(GOLDEN_FX)
    from engine.strategies.v2.invariants import InvariantRule

    inv.rules.append(
        InvariantRule(id="INV_MAX_LEV", kind="max_leverage", params={"max": 2.0})
    )
    v2.risk.leverage_limit = 10.0
    violations = inv.check_spec(risk=v2.risk.model_dump(), stop_type=v2.stop_loss.type)
    assert any("INV_MAX_LEV" in v for v in violations)


def test_compiler_refuses_live():
    v2, _, _ = migrate_v1_file_to_v2(GOLDEN_FX)
    data = v2.canonical_dict()
    data["compatibility"]["permitted_environments"] = ["BACKTEST", "LIVE"]
    data["metadata"]["user_approved"] = True
    live_spec = validate_spec_v2(data)
    with pytest.raises(SpecV2Error, match="LIVE"):
        compile_spec_v2_deterministic(live_spec)


def test_no_nautilus_import_in_v2_domain():
    import engine.strategies.v2 as v2pkg
    import inspect

    src = Path(inspect.getfile(v2pkg)).parent
    for py in src.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "nautilus_trader" not in text, py.name
        assert "from nautilus" not in text, py.name

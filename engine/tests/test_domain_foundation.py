"""QLN-1 Domain Foundation contract / schema tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine.domain import (
    EXAMPLE_IS_NOT_DEFAULT,
    LIVE_DEFAULT_DENY,
    STRATEGY_DEFAULT_SEMANTICS,
    AuditAction,
    AuditEvent,
    BacktestEngineContract,
    DomainEntityKind,
    Environment,
    EvidenceStage,
    ExecutionMode,
    HashKind,
    StrategyLifecycle,
    VersionBump,
    assert_environment_allowed,
    assert_evidence_transition,
    assert_example_not_default,
    assert_lifecycle_transition,
    audit_event_to_dict,
    canonical_json_bytes,
    classify_strategy_change,
    compute_hash,
    fingerprint_engine,
    hash_config,
    hash_strategy_definition,
    map_legacy_environment,
    map_legacy_execution_channel,
    map_legacy_paper_run_status,
    map_legacy_strategy_lifecycle,
    new_domain_id,
    next_strategy_version,
    normalize_environment,
    parse_domain_id,
)
from engine.domain.defaults import (
    CANONICAL_EMA_DEFAULT_FAST,
    CANONICAL_EMA_DEFAULT_SLOW,
    format_ema_label,
)
from engine.domain.engine_contracts import SHARED_STRATEGY_FIELD_SEMANTICS
from engine.domain.enums import DomainError
from engine.domain.environment import EnvironmentGateError
from engine.domain.legacy_mapping import (
    ASSET_DISPOSITIONS,
    ENVIRONMENT_LEGACY,
    STRATEGY_LIFECYCLE_LEGACY,
)
from engine.paper.signal_engine import EmaSignalEngine
from engine.trading.execution_environment import (
    ExecutionEnvironment,
    assert_environment_allowed as legacy_assert_environment_allowed,
)


DOMAIN_ROOT = Path(__file__).resolve().parents[1] / "domain"


def test_domain_ids_immutable_and_parseable():
    a = new_domain_id(DomainEntityKind.STRATEGY, seed="alpha")
    b = new_domain_id(DomainEntityKind.STRATEGY, seed="alpha")
    c = new_domain_id(DomainEntityKind.STRATEGY, seed="beta")
    assert a.value == b.value
    assert a.value != c.value
    assert parse_domain_id(a.value).kind == DomainEntityKind.STRATEGY
    with pytest.raises(ValueError):
        parse_domain_id("not-an-id")


def test_lifecycle_transitions_fail_closed():
    assert_lifecycle_transition(StrategyLifecycle.IDEA, StrategyLifecycle.DRAFT)
    with pytest.raises(DomainError):
        assert_lifecycle_transition(StrategyLifecycle.IDEA, StrategyLifecycle.LIVE_APPROVED)
    with pytest.raises(DomainError):
        assert_lifecycle_transition(StrategyLifecycle.RETIRED, StrategyLifecycle.DRAFT)


def test_evidence_stage_no_skip():
    assert_evidence_transition(EvidenceStage.E1_BACKTEST, EvidenceStage.E2_OOS)
    with pytest.raises(DomainError):
        assert_evidence_transition(EvidenceStage.E1_BACKTEST, EvidenceStage.E4_PAPER)


def test_environment_vs_execution_mode_distinct():
    assert Environment.PAPER is not ExecutionMode.PAPER
    assert StrategyLifecycle.DRAFT.value not in {e.value for e in Environment}


def test_live_default_deny():
    assert LIVE_DEFAULT_DENY is True
    with pytest.raises(EnvironmentGateError):
        assert_environment_allowed("LIVE", live_allowed=False)
    assert normalize_environment("SANDBOX") == Environment.PAPER
    assert map_legacy_environment("SANDBOX") == Environment.PAPER


def test_legacy_execution_environment_facade_preserves_sandbox():
    env = legacy_assert_environment_allowed("SANDBOX")
    assert env == ExecutionEnvironment.SANDBOX
    with pytest.raises(EnvironmentGateError):
        legacy_assert_environment_allowed("LIVE")


def test_hash_determinism_and_secret_exclusion():
    payload = {
        "ema_fast": 10,
        "created_at": "2020-01-01",
        "api_key": "should-not-hash",
        "nested": {"token": "x", "ok": 1},
    }
    h1 = hash_strategy_definition(payload)
    h2 = hash_strategy_definition(
        {"nested": {"ok": 1}, "ema_fast": 10, "created_at": "2099-01-01", "api_key": "other"}
    )
    assert h1 == h2
    raw = canonical_json_bytes(payload).decode()
    assert "api_key" not in raw
    assert "token" not in raw
    assert "created_at" not in raw
    assert compute_hash(HashKind.CONFIG, {"a": 1}) == hash_config({"a": 1})
    assert fingerprint_engine(
        engine_name="nautilus", engine_version="1.231.0", adapter_version="v1"
    )


def test_audit_event_rejects_secret_metadata():
    with pytest.raises(ValueError):
        AuditEvent(
            action=AuditAction.UPDATE,
            target_kind="strategy",
            target_id="x",
            metadata={"api_key": "nope"},
        )
    ev = AuditEvent(
        action=AuditAction.TRANSITION,
        target_kind="strategy",
        target_id="x",
        previous_state="DRAFT",
        new_state="STATIC_VALIDATED",
        environment="BACKTEST",
        correlation_id="corr-1",
    )
    d = audit_event_to_dict(ev)
    assert d["action"] == "TRANSITION"
    assert d["timestamp_utc"]


def test_version_semantics():
    _cls, bump = classify_strategy_change(
        changes_trading_behavior=True,
        changes_risk_limits=False,
        changes_broker_or_secret=False,
        display_only=False,
    )
    assert bump == VersionBump.MINOR
    assert next_strategy_version("v1", VersionBump.MINOR) in {"v1.1", "v1.1.0"}
    assert next_strategy_version("v1.2", VersionBump.NONE).startswith("v")


def test_legacy_mapping_complete_tables():
    assert map_legacy_strategy_lifecycle("PAPER_READY") == StrategyLifecycle.PAPER_APPROVED
    assert map_legacy_execution_channel("vnpy") == ExecutionMode.NO_EXECUTION
    assert map_legacy_paper_run_status("RUNNING") == "RUN.RUNNING"
    assert len(STRATEGY_LIFECYCLE_LEGACY) >= 5
    assert len(ENVIRONMENT_LEGACY) >= 5
    assert len(ASSET_DISPOSITIONS) >= 8


def test_shared_strategy_field_semantics_cover_required_keys():
    required = {
        "instrument",
        "timeframe",
        "parameters",
        "direction",
        "position_sizing",
        "risk_settings",
        "stop_loss",
        "take_profit",
        "trading_session",
        "fees",
        "slippage",
        "clock_timezone",
        "data_source",
        "execution_assumptions",
    }
    assert required <= set(SHARED_STRATEGY_FIELD_SEMANTICS)


def test_strategy_default_semantics_one_source():
    assert STRATEGY_DEFAULT_SEMANTICS == "ONE_CANONICAL_SOURCE"
    assert EXAMPLE_IS_NOT_DEFAULT is True
    assert_example_not_default()
    assert CANONICAL_EMA_DEFAULT_FAST == 10
    assert CANONICAL_EMA_DEFAULT_SLOW == 20
    assert format_ema_label(10) == "EMA10"


def test_signal_engine_labels_match_periods_not_hardcoded_60():
    eng = EmaSignalEngine(fast=10, slow=20)
    for p in range(25):
        eng.update(100.0 + p * 0.5, timestamp="t", instrument="BTCUSDT")
    d = eng.update(120.0, timestamp="t2", instrument="BTCUSDT")
    assert "EMA60" not in d.condition_values
    assert "EMA60" not in "".join(d.conditions)


def test_domain_package_does_not_import_nautilus_trader():
    for path in DOMAIN_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("nautilus_trader"), path
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("nautilus_trader"), path


def test_backtest_engine_contract_runtime_checkable():
    from engine.nautilus.domain_adapter import NautilusBacktestPort

    port = NautilusBacktestPort()
    assert isinstance(port, BacktestEngineContract)
    caps = port.capabilities()
    assert caps.supports_backtest is True
    assert caps.supports_live is False


def test_enum_uniqueness_within_each_domain():
    for enum_cls in (StrategyLifecycle, EvidenceStage, Environment, ExecutionMode):
        values = [e.value for e in enum_cls]
        assert len(values) == len(set(values)), enum_cls


def test_no_duplicate_canonical_lifecycle_environment_collision():
    lifecycle_vals = {e.value for e in StrategyLifecycle}
    env_vals = {e.value for e in Environment}
    assert "PAPER" not in lifecycle_vals
    assert "LIVE" not in lifecycle_vals
    assert "BACKTEST" not in lifecycle_vals
    assert lifecycle_vals.isdisjoint(env_vals)

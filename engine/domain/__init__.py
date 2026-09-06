"""QuantLab Canonical Domain Foundation (QLN-1).

SSOT for strategy / experiment / evidence / run / version concepts.
Does NOT implement Experiment Ledger, Spec v2, Evidence Pipeline, Shadow, or Live.
"""

from __future__ import annotations

from engine.domain.audit import AuditAction, AuditEvent, audit_event_to_dict
from engine.domain.defaults import (
    CANONICAL_EMA_DEFAULT_FAST,
    CANONICAL_EMA_DEFAULT_SLOW,
    EXAMPLE_IS_NOT_DEFAULT,
    STRATEGY_DEFAULT_SEMANTICS,
    assert_example_not_default,
)
from engine.domain.engine_contracts import (
    BacktestEngineContract,
    BacktestRequest,
    BacktestResultContract,
    EngineCapability,
    PaperRuntimeContract,
    PaperRuntimeRequest,
    RuntimeResultContract,
)
from engine.domain.enums import (
    EvidenceStage,
    ExecutionMode,
    StrategyLifecycle,
    assert_evidence_transition,
    assert_lifecycle_transition,
    evidence_order_index,
)
from engine.domain.environment import (
    LIVE_DEFAULT_DENY,
    Environment,
    assert_environment_allowed,
    normalize_environment,
)
from engine.domain.hashing import (
    HashKind,
    canonical_json_bytes,
    compute_hash,
    fingerprint_engine,
    hash_config,
    hash_dataset_payload,
    hash_strategy_definition,
)
from engine.domain.ids import (
    DomainEntityKind,
    DomainId,
    new_domain_id,
    parse_domain_id,
)
from engine.domain.legacy_mapping import (
    LegacyDisposition,
    map_legacy_environment,
    map_legacy_execution_channel,
    map_legacy_paper_run_status,
    map_legacy_strategy_lifecycle,
)
from engine.domain.versioning import (
    ChangeClass,
    VersionBump,
    classify_strategy_change,
    next_strategy_version,
)

__all__ = [
    "AuditAction",
    "AuditEvent",
    "BacktestEngineContract",
    "BacktestRequest",
    "BacktestResultContract",
    "CANONICAL_EMA_DEFAULT_FAST",
    "CANONICAL_EMA_DEFAULT_SLOW",
    "ChangeClass",
    "DomainEntityKind",
    "DomainId",
    "EXAMPLE_IS_NOT_DEFAULT",
    "EngineCapability",
    "Environment",
    "EvidenceStage",
    "ExecutionMode",
    "HashKind",
    "LIVE_DEFAULT_DENY",
    "LegacyDisposition",
    "PaperRuntimeContract",
    "PaperRuntimeRequest",
    "RuntimeResultContract",
    "STRATEGY_DEFAULT_SEMANTICS",
    "StrategyLifecycle",
    "VersionBump",
    "assert_environment_allowed",
    "assert_evidence_transition",
    "assert_example_not_default",
    "assert_lifecycle_transition",
    "audit_event_to_dict",
    "canonical_json_bytes",
    "classify_strategy_change",
    "compute_hash",
    "evidence_order_index",
    "fingerprint_engine",
    "hash_config",
    "hash_dataset_payload",
    "hash_strategy_definition",
    "map_legacy_environment",
    "map_legacy_execution_channel",
    "map_legacy_paper_run_status",
    "map_legacy_strategy_lifecycle",
    "new_domain_id",
    "next_strategy_version",
    "normalize_environment",
    "parse_domain_id",
]

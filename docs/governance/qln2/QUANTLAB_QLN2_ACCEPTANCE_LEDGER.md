# QLN-2 Acceptance Ledger

```text
PHASE=QLN-2
QLN_2=PASS
STRATEGY_SPEC_V2=PASS
STRATEGY_CONTRACT=PASS
STRATEGY_INVARIANTS=PASS
V1_TO_V2_MIGRATION=PASS
GOLDEN_STRATEGY_SEMANTIC_DRIFT=0
STRATEGY_PACKAGE=PASS
EXPORT_IMPORT_HASH=PASS
PACKAGE_SECRET_COUNT=0
SEMANTIC_DIFF=PASS
VERSION_LINEAGE=PASS
CODE_ESCAPE_HATCH_CONTRACT=PASS
NAUTILUS_ADAPTER_COMPILER=PASS
SPEC_TO_ADAPTER_DETERMINISTIC=PASS
INVALID_SPEC_FAIL_CLOSED=PASS
DOMAIN_SCHEMA_TESTS=PASS
CONTRACT_TESTS=PASS
REGRESSION=PASS
NO_SILENT_TEST_LOSS=YES
SIMILAR_ISSUE_AUDIT=PASS
UNAUTHORIZED_SCOPE_EXPANSION=NO
PERSISTENT_DB_SCHEMA_CHANGE=NONE
QLN_3_STARTED=NO
NEXT_PHASE_AUTO_ENTER=NO
```

## Gate detail

| Gate | Evidence | Result |
|---|---|---|
| STRATEGY_SPEC_V2 | `StrategySpecV2` covers identity/metadata/universe/timeframe/data/signal/entry-exit/sizing/risk/stops/TP/trailing fields/session/fees/slippage/execution/direction/parameters/invariants refs/extensions/version/lineage | PASS |
| STRATEGY_CONTRACT | WHAT/WHY/WHEN/WHEN_NOT/RISK/INVALIDATION/EXPECTED/ABNORMAL/RETIREMENT — contract only | PASS |
| STRATEGY_INVARIANTS | Structured `InvariantRule` kinds (martingale, avg-down, leverage, stale/unknown exec, max positions, …) | PASS |
| V1_TO_V2_MIGRATION | `migrate_v1_to_v2` + `assert_semantic_drift_zero` on golden FX + BTC | PASS |
| GOLDEN_STRATEGY_SEMANTIC_DRIFT | Identity/params/signal/entry/exit/risk/sizing/slippage checked = 0 drift | PASS |
| STRATEGY_PACKAGE | manifest + spec + contract + invariants + parameters + data_requirements + lineage + README | PASS |
| EXPORT_IMPORT_HASH | export → import → hash match; tamper → fail closed | PASS |
| PACKAGE_SECRET_COUNT | Broker/AI/DB/token/env patterns rejected; policy flag `secrets_forbidden` not false-positive | PASS |
| SEMANTIC_DIFF | Classes: metadata / parameter / logic / risk / data / execution / breaking | PASS |
| VERSION_LINEAGE | family/version/parent/derived/fork/parameter-vs-logic child; QLN-1 `versioning` helpers | PASS |
| CODE_ESCAPE_HATCH_CONTRACT | capability allowlist; must respect contract+invariants; secrets forbidden | PASS |
| NAUTILUS_ADAPTER_COMPILER | Spec→domain_adapter→nautilus_params dict; no Nautilus class imports in v2 package | PASS |
| SPEC_TO_ADAPTER_DETERMINISTIC | Same Spec → identical compile dict; v1/v2 `nautilus_params` parity on goldens | PASS |
| INVALID_SPEC_FAIL_CLOSED | missing id, illegal LIVE, bad drawdown, empty contract when/when_not/invalidation, empty invariants, hash mismatch, malformed hatch | PASS |
| Tests | `test_strategy_spec_v2.py` **16 passed**; `test_domain_foundation.py` **19 passed**; engine collect **171** (pre-QLN-2 **155**) | PASS |
| UNAUTHORIZED_SCOPE_EXPANSION | No Experiment Ledger / Evidence / Paper / Shadow / Live / UI / DB migration | NO |

## Pre-declared numerical execution deltas

None required for QLN-2 Spec→Adapter params parity. Runtime fill/latency differences remain engine-layer and are out of Spec asset scope.

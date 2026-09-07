# QLN-3 Acceptance Ledger

```text
PHASE=QLN-3
QLN_3=PASS
REPRODUCIBILITY_CORE=PASS
EXPERIMENT_LEDGER=PASS
DATASET_VERSION_HASH=PASS
TIME_GOVERNANCE=PASS
DATA_PROVENANCE=PASS
FEE_SLIPPAGE_EXEC_ASSUMPTIONS=PASS
ENGINE_VERSION_LOGGING=PASS
COST_ATTRIBUTION=PASS
RANDOM_SEED=PASS
ARTIFACT_HASHES=PASS
ONE_CLICK_REPRODUCE=PASS
DATA_TRUST_GATE=PASS
GOLDEN_REPRODUCE=PASS
INVALID_TRUST_FAIL_CLOSED=PASS
LEDGER_IMMUTABLE=PASS
TOLERANCES_PREDECLARED=YES
DOMAIN_SCHEMA_TESTS=PASS
CONTRACT_TESTS=PASS
REGRESSION=PASS
NO_SILENT_TEST_LOSS=YES
SIMILAR_ISSUE_AUDIT=PASS
UNAUTHORIZED_SCOPE_EXPANSION=NO
PERSISTENT_DB_SCHEMA_CHANGE=NONE
QLN_4_STARTED=NO
```

## Gate detail

| Gate | Evidence | Result |
|---|---|---|
| EXPERIMENT_LEDGER | Append-only JSONL; duplicate id rejected; content_hash integrity | PASS |
| DATASET_VERSION_HASH | `dataset_id` / `dataset_version` / `dataset_hash` on every sealed record | PASS |
| TIME_GOVERNANCE | `TimeGovernance` frozen; tz-aware/monotonic/dup fail closed | PASS |
| DATA_PROVENANCE | Via Data Trust → DataGate provenance | PASS |
| FEE/SLIPPAGE/EXEC | `ExecutionAssumptions` sealed into record | PASS |
| ENGINE_VERSION | `engine_name/version/adapter_version` + `fingerprint_engine` | PASS |
| COST_ATTRIBUTION | `CostAttribution` on record | PASS |
| RANDOM_SEED | Required field; reproduce requires identical seed | PASS |
| ARTIFACT_HASHES | metrics + dataset hashes | PASS |
| ONE_CLICK_REPRODUCE | `reproduce_experiment` → `REPRODUCE=PASS` | PASS |
| DATA_TRUST_GATE | Mandatory; WARN/FAIL → cannot seal | PASS |
| GOLDEN_REPRODUCE | Same golden EMA experiment within `qln3_golden_tol_v1` | PASS |
| TOLERANCES | Pre-declared in `engine/experiment/tolerances.py` — no post-hoc excuse | PASS |

## Pre-declared tolerances (`qln3_golden_tol_v1`)

| Metric | Abs tolerance |
|---|---|
| total_return | 1e-12 |
| max_drawdown | 1e-12 |
| final_equity | 1e-9 |
| sharpe | 1e-9 |
| trade_count | 0 (exact) |
| dataset/config/strategy/seed | identical |

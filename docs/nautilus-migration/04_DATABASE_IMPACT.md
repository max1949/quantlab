# 04 — Database Impact (Phase 0)

## Current relevant tables

| Table | Notes |
|-------|-------|
| `factors` | versioned JSON `spec` |
| `backtests` | factor-centric; **no `engine` column today** |
| `validations` | OOS / WF / sensitivity / robustness JSON |
| `research_reports` | narrative + `based_on` |
| `data_snapshots` | reproducibility |
| `paper_orders` / `paper_order_events` | `channel` string includes `vnpy` |
| users / orgs / billing / … | out of scope |

## Planned additive changes (NOT applied in Phase 0)

1. **`backtests.engine`** (nullable → default for new rows `NAUTILUS`; historical NULL or `VECTORIZED_LEGACY`)
2. Optional **`backtests.engine_version`**
3. Future **`strategy_specs`** / **`strategy_spec_versions`** tables
4. Future **`data_provenance`** metadata
5. Do **not** rewrite historical `channel='vnpy'` rows; treat as `VNPY_LEGACY` semantics in reports

## Discipline

```text
backup → migration → upgrade → downgrade test
nullable / backwards-compatible first
no blind DROP of vnpy-related historical values
```

## Phase 0 DB actions

```text
NO_MIGRATION_APPLIED = TRUE
NO_PRODUCTION_SCHEMA_CHANGE = TRUE
```

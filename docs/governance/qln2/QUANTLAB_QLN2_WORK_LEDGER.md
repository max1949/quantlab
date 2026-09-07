# QLN-2 Work Ledger

```text
PHASE=QLN-2
TITLE=Strategy Spec v2 / Strategy Contract / Portable Package
OWNER_AUTHORIZATION=YES
QLN_0=PASS
QLN_1=PASS
QLN_1_OPEN_IN_PHASE=NONE
AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES
ENGINEERING_START=ALLOW
PERSISTENT_DB_SCHEMA_CHANGE=DENY
EXPERIMENT_LEDGER_BUILD=NO
EVIDENCE_PIPELINE_BUILD=NO
PAPER_EXPANSION=NO
SHADOW_BUILD=NO
LIVE_BUILD=NO
UI_EXPANSION=NO
AUTO_NEXT_QLN=NO
```

## Scope executed

| Workstream | Path / artifact | Status |
|---|---|---|
| Spec v2 schema | `engine/strategies/v2/spec_v2.py` | DONE |
| Strategy Contract | `engine/strategies/v2/contract.py` | DONE |
| Strategy Invariants | `engine/strategies/v2/invariants.py` | DONE |
| V1→V2 migration | `engine/strategies/v2/migrate.py` | DONE |
| Portable package | `engine/strategies/v2/package.py` | DONE |
| Secret scanner | `engine/strategies/v2/secrets.py` | DONE |
| Semantic diff | `engine/strategies/v2/semantic_diff.py` | DONE |
| Version / lineage | `engine/strategies/v2/lineage.py` (QLN-1 versioning aligned) | DONE |
| Code escape hatch | `engine/strategies/v2/escape_hatch.py` | DONE |
| Nautilus adapter compiler | `engine/strategies/v2/compiler.py` (no `nautilus_trader` import) | DONE |
| Golden examples | `strategy_specs/examples/*.v2.json` + `*.v2.package.json` | DONE |
| Tests | `engine/tests/test_strategy_spec_v2.py` | DONE |

## Explicit non-goals (preserved)

- Experiment Ledger / Evidence Pipeline / Paper·Shadow·Live expansion
- Persistent DB schema / Alembic
- UI expansion / Marketplace / Production deploy
- Auto-enter QLN-3

## Structural DB

```text
QLN_2_STRUCTURAL_DB_CHANGE_REQUIRED=NO
```

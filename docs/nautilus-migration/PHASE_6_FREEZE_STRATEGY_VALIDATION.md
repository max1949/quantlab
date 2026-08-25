# Phase 6 Freeze → Strategy Validation

```text
PHASE_6_STATUS=CLOSED
FINAL_ACCEPTANCE=20/20 PASS
ENGINEERING_MODE=MAINTENANCE_ONLY
NEXT_MODE=STRATEGY_VALIDATION

LIVE_EXECUTION=DENY
PHASE_7_AUTO_ENTER=DENY
DO_NOT_ENTER_PHASE_7
DO_NOT_ENABLE_LIVE
```

## Frozen (except P0/P1)

- New Paper product features
- New execution engines
- Real-money broker / exchange adapters
- LIVE enablement
- Complex UI / unvalidated APIs
- Large architecture refactors
- Speculative “maybe later” features
- Auto-enter Phase 7

## P2 (not blockers)

1. Production `NO_GIT` — keep DEPLOY_COMMIT + backup + rollback; defer git-on-prod.
2. `scripts/update-oracle.sh` — `LEGACY_ORACLE_DEPLOY_SCRIPT=DEPRECATED`, `TENCENT_PRODUCTION_USE=DENY`.

## Success metric shift

```text
BUILD_LESS / TEST_MORE / STRATEGIES_OVER_FEATURES / EVIDENCE_OVER_COMPLEXITY
```

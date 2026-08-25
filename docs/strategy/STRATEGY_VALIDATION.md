# Strategy Validation (authoritative mode after Phase 6 close)

```text
PHASE_6_STATUS=CLOSED
ENGINEERING_MODE=MAINTENANCE_ONLY
NEXT_MODE=STRATEGY_VALIDATION
LIVE_EXECUTION=DENY
PHASE_7=DENY
```

## Goal

Use the existing Research → Backtest → Paper → Evaluation loop to
**find, reject, and validate** strategies with real statistical edge.

Not: more product features. Not: Phase 7. Not: LIVE.

## Pipeline (no skip levels)

```text
Idea → Spec → Historical Backtest → OOS → Walk Forward
  → Robustness → Parameter Stability → Cost / Slippage Stress
  → Paper Sandbox → Backtest vs Paper Parity → Evaluation
  → PROMOTE | HOLD | REJECT
```

## Outcomes

| Decision | Meaning |
|----------|---------|
| PROMOTE | OOS + WF + Robustness + Cost + Paper + Parity all PASS; overfit ≠ HIGH |
| HOLD | Evidence incomplete (e.g. Paper window too short) — do not retune to chase |
| REJECT | Hard fail / clear overfit — write Strategy Graveyard |

`BACKTEST_PROFITABLE ≠ STRATEGY_VALID`. AI may analyze; **gate decides**.

## Implementation map

| Piece | Path |
|-------|------|
| Gate decision | `engine/validation/decision.py` |
| Pipeline | `engine/validation/pipeline.py` |
| Baseline library | `engine/validation/baselines.py` |
| Graveyard | `engine/validation/graveyard.py` → `data/strategy_graveyard/` |
| Batch runner | `scripts/run_strategy_validation_batch.py` |
| Legacy lifecycle card | `engine/strategies/lifecycle.py` (still used by AI MVP; batch uses validation package) |

## Cost stress

`BASE_COST` / `1.5X_COST` / `2X_COST` on fee + slippage. Mild cost death → `COST_ROBUSTNESS=FAIL`.

## Paper / parity (batch 001)

Batch 001 marks Paper and Parity as **INSUFFICIENT** until a dedicated Paper
observation window exists. That blocks PROMOTE by design (no skip-level).

## Deploy scripts

```text
LEGACY_ORACLE_DEPLOY_SCRIPT=DEPRECATED
TENCENT_PRODUCTION_USE=DENY
```

`scripts/update-oracle.sh` refuses unless `QUANTLAB_FORCE_LEGACY_ORACLE=1`
(legacy Oracle host only). Tencent prod remains `/srv/quantlab` + DEPLOY_COMMIT marker.

## Owner freeze

```text
DO_NOT_ENTER_PHASE_7
DO_NOT_ENABLE_LIVE
ENGINEERING_CHANGE=DENY  (except P0/P1)
```

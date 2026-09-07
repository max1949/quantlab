# QLN-4 Work Ledger

```text
PHASE=QLN-4
TITLE=Evidence Validation Core
CAMPAIGN=QUANTLAB_QLN_3_TO_10_AUTONOMOUS_CAMPAIGN
QLN_4_ENTRY_GATE=PASS
PREAUTHORIZATION_REFERENCE=QUANTLAB_QLN_3_TO_10_AUTONOMOUS_CAMPAIGN
PREVIOUS_PHASE_CLOSURE=QLN-3@64d7a64
AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES
EVIDENCE_PIPELINE_BUILD=YES
THRESHOLD_RELAXATION=DENY
LIVE_BUILD=NO
REAL_MONEY=NO
```

## Scope

| Workstream | Path | Status |
|---|---|---|
| Evidence pipeline | `engine/evidence/pipeline.py` | DONE |
| Fee / slippage / regime / extreme stresses | `engine/evidence/stresses.py` | DONE |
| Reality Score | `engine/evidence/reality.py` | DONE |
| Research Debt | `engine/evidence/debt.py` | DONE |
| Promotion / Kill rules (PROMOTE/HOLD/KILL) | `engine/evidence/rules.py` | DONE |
| Frozen thresholds | `engine/evidence/thresholds.py` (`qln4_evidence_thr_v1`) | DONE |
| Tests | `engine/tests/test_evidence_pipeline_qln4.py` | DONE |

Reuses QLN-era walk_forward / backtest / validation overfit helpers; does not lower legacy Sprint thresholds via silent rewrite.

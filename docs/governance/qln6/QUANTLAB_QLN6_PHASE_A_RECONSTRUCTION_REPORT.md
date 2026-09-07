# QLN-6 Phase A — Historical Strategy Reconstruction

```text
ACTIVITY=QLN_6_GENUINE_STRATEGY_RECONSTRUCTION_AND_RESEARCH_SEED
PHASE=A
QLN_6_STARTED_AT_PHASE_A=NO
HISTORICAL_BACKTESTS_INSPECTED=23
FULL_STRATEGY_SEMANTICS_RECOVERABLE=YES (for template factors + platform sign rule)
GENUINE_HISTORICAL_STRATEGIES_RECOVERED=4
NEW_GENUINE_RESEARCH_STRATEGIES_CREATED=0
PHASE_B_EXECUTED=NO (recovered >= 2)
AUTO_GENERATE_STRATEGY_TO_PASS_GATE=NO
THRESHOLD_RELAXATION=NO
OPTIMIZE_UNTIL_PASS=NO
```

## Recoverability basis

Factor Lab `backtests` bind `factor_id` + `symbol` + `cost_config`.  
Platform execution contract (historical SSOT):

`engine/backtest.py` → `position = sign(signal)`; returns use **lagged** position (no lookahead).

Template factor params recovered from `factors.spec`.  
**Not** AI-invented entry/exit beyond this documented contract.

## Distinct recovered definitions

| strategy_id | template | params | historical symbols | evidence dataset |
|---|---|---|---|---|
| hist_fl_momentum_w20 | momentum | window=20 | AU, RB (seed hist) | CU_1d genuine |
| hist_fl_momentum_w250 | momentum | window=250 | IF (seed hist) | CU_1d genuine |
| hist_fl_mean_reversion_w20 | mean_reversion | window=20 | RB | MA_1d genuine |
| hist_fl_rsi_w14 | rsi | window=14 | AU | CU_1d genuine |

Packages: `strategy_specs/historical_reconstructed/*.v2.package.json`

## Evidence results (frozen thresholds `qln4_evidence_thr_v1`)

| strategy_id | decision | higher_evidence | notes |
|---|---|---|---|
| hist_fl_momentum_w20 | KILL | NO | OOS/WF/stress FAIL |
| hist_fl_momentum_w250 | HOLD | YES | OOS+WF PASS; sensitivity INSUFFICIENT |
| hist_fl_mean_reversion_w20 | KILL | NO | WF/stress FAIL |
| hist_fl_rsi_w14 | PROMOTE | YES | All core gates PASS |

```text
STRATEGIES_FULLY_EVALUATED=4
PROMOTE=1
HOLD=1
KILL=2
NO_EDGE_FOUND=2
HIGHER_EVIDENCE_STRATEGY_COUNT=2
REAL_RESEARCH_DEMAND=YES
```

### Integrity note (not a threshold change)

`hist_fl_rsi_w14` preserves historical `sign(raw RSI)` which is nearly always long. PROMOTE is under frozen gates on genuine CU data — recorded as research risk / possible regime artifact, **not** discarded to cherry-pick.

## PaperRun

Canonical PaperRun path is Spec→EMA/`paper_node`. Factor-sign Specs are **not** eligible for that runner without inventing an adapter.  

```text
PAPER_QUALIFIED=0
PAPER_STATUS=INSUFFICIENT_PATH (honest; no fake Paper PASS)
```

## Gate re-evaluation

```text
MULTIPLE_HIGHER_EVIDENCE_STRATEGIES=YES
REAL_RESEARCH_DEMAND=YES
QLN_6_ENTRY_GATE=PASS
CAMPAIGN_RESUMED=YES
QLN_6_STARTED=NO
PHASE_B_EXECUTED=NO
REAL_MONEY=NO
STOP=NO
```

Artifact: `docs/governance/qln6/artifacts/phase_a_evidence_results.json`  
Formal seal: `QUANTLAB_QLN6_GENUINE_STRATEGY_RECONSTRUCTION_AND_RESEARCH_SEED_LEDGER.md`

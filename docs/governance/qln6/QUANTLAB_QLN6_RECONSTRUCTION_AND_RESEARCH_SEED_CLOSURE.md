# QLN-6 — Genuine Strategy Reconstruction & Research Seed (Closure)

```text
ACTIVITY=QLN_6_GENUINE_STRATEGY_RECONSTRUCTION_AND_RESEARCH_SEED
QLN_6_STARTED=NO
REAL_MONEY=NO
AUTO_GENERATE_STRATEGY_TO_PASS_GATE=NO
OPTIMIZE_UNTIL_PASS=NO
THRESHOLD_RELAXATION=NO
CHERRY_PICK_PERIOD=NO
LOOKAHEAD=NO
DATA_SNOOPING_TO_GATE=NO
```

## Phase A — Historical reconstruction

```text
HISTORICAL_BACKTESTS_INSPECTED=23
FULL_STRATEGY_SEMANTICS_RECOVERABLE=YES
  (platform contract: position=sign(signal), lagged returns; factor template params from Factor Lab)
GENUINE_HISTORICAL_STRATEGIES_RECOVERED=4
ORIGINAL_SEMANTICS_PRESERVED=YES
PHASE_B_EXECUTED=NO
NEW_GENUINE_RESEARCH_STRATEGIES_CREATED=0
```

Recovered distinct definitions (not one Spec per backtest row):

| strategy_id | decision | higher_evidence |
|---|---|---|
| hist_fl_momentum_w20 | KILL | NO |
| hist_fl_momentum_w250 | HOLD | YES |
| hist_fl_mean_reversion_w20 | KILL | NO |
| hist_fl_rsi_w14 | PROMOTE | YES |

Evidence path: Experiment Ledger → Data Trust → Canonical Backtest → OOS → Walk Forward → Stress → Reality Score → Research Debt → PROMOTE/HOLD/KILL.  
PaperRun: `PAPER_QUALIFIED=0` (canonical EMA/`paper_node` path; no invented adapter).

## Phase B — Research seeding

Skipped: recovered ≥ 2 genuine historical strategies (`INITIAL_RESEARCH_CANDIDATE_CAP` unused).

## Entry Gate re-evaluation

```text
GENUINE_STRATEGY_COUNT=4
STRATEGIES_FULLY_EVALUATED=4
PROMOTE=1
HOLD=1
KILL=2
NO_EDGE_FOUND=2
HIGHER_EVIDENCE_STRATEGY_COUNT=2
REAL_RESEARCH_DEMAND=YES
MULTIPLE_HIGHER_EVIDENCE_STRATEGIES=YES
QLN_6_ENTRY_GATE=PASS
CAMPAIGN_RESUMED=YES
QLN_6_STARTED=NO
STOP=NO
```

Constitution Entry satisfied without inventing strategies. Campaign may resume **QLN-6 engineering** under existing Owner preauthorization; this activity itself does not stamp `QLN_6_STARTED=YES`.

## Artifacts

- Report: `docs/governance/qln6/QUANTLAB_QLN6_PHASE_A_RECONSTRUCTION_REPORT.md`
- Results: `docs/governance/qln6/artifacts/phase_a_evidence_results.json`
- Packages: `strategy_specs/historical_reconstructed/*.v2.package.json`
- DNA scaffolding (prep, not Entry stamp): `engine/strategy_dna/`
- Research memory seed: `data/research_memory/` (local runtime)

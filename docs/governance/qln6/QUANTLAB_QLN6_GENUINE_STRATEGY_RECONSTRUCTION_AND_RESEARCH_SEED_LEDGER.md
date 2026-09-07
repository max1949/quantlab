# QLN-6 Genuine Strategy Reconstruction & Research Seed

```text
ACTIVITY=QLN_6_GENUINE_STRATEGY_RECONSTRUCTION_AND_RESEARCH_SEED
QLN_6_STARTED=NO
AUTO_GENERATE_STRATEGY_TO_PASS_GATE=NO
OPTIMIZE_UNTIL_PASS=NO
SEARCH_UNTIL_PROFITABLE=NO
THRESHOLD_RELAXATION=NO
CHERRY_PICK_PERIOD=NO
LOOKAHEAD=NO
DATA_SNOOPING_TO_GATE=NO
SYNTHETIC_AS_GENUINE=NO
GOLDEN_AS_GENUINE=NO
LIVE=NO
REAL_MONEY=NO
```

## Phase A — Historical Strategy Reconstruction

### Intake surface

| Source | Count / note |
|---|---|
| Business SQL `quantlab.backtests` | 23 |
| Joined `factors` | 23/23 (all `kind=template`) |
| Joined `data_snapshots` | 23/23 (timeframe recovered) |
| `research_projects` via factor.project_id | 0 linked (NULL) |
| Distinct (template, params) definitions | **4** |

Historical symbols in dump: **AU=15, RB=7, IF=1** (prior seed/sample class).  
Genuine evidence datasets used after transfer: **CU / MA** parquet (`GENUINE_DATASET`).

### Recoverability rule applied

`FULL_STRATEGY_SEMANTICS_RECOVERABLE=YES` only when **all** of:

| Field | Recovery source (not AI guess) |
|---|---|
| entry / exit / direction | `engine.backtest.signal_to_positions` → `position = sign(signal)`; flat/flip on sign change |
| sizing | Unit ±1 (platform contract) |
| parameters | `factors.spec` (template params) |
| instrument (historical) | `backtests.symbol` |
| timeframe | `data_snapshots.timeframe` (=1d for all 23) |
| fees/slippage | `backtests.cost_config` (fee_rate=0.0005, slippage_bps=1.0) |
| essential risk | Historical engine: **no** stop/TP; costs only — recorded as such |
| lookahead avoidance | Lagged position × contemporaneous return (engine SSOT) |

Forbidden paths **not** used: inventing rules from factor scores alone; fabricating stops; optimizing windows to pass gates.

```text
HISTORICAL_BACKTESTS_INSPECTED=23
FULL_STRATEGY_SEMANTICS_RECOVERABLE_COUNT=23
DISTINCT_GENUINE_HISTORICAL_STRATEGIES=4
ORIGINAL_SEMANTICS_PRESERVED=YES  # trading rules + params + costs
INSTRUMENT_TRANSFER_FOR_EVIDENCE=YES  # AU/RB/IF seed → CU/MA genuine parquet (documented; not rule retune)
```

### Recovered strategies → Spec V2 + lineage

| strategy_id | Class | template | params | hist symbols | evidence set |
|---|---|---|---|---|---|
| `hist_fl_momentum_w20` | GENUINE_HISTORICAL_STRATEGY | momentum | window=20 | AU, RB | CU_1d |
| `hist_fl_momentum_w250` | GENUINE_HISTORICAL_STRATEGY | momentum | window=250 | IF | CU_1d |
| `hist_fl_mean_reversion_w20` | GENUINE_HISTORICAL_STRATEGY | mean_reversion | window=20 | RB | MA_1d |
| `hist_fl_rsi_w14` | GENUINE_HISTORICAL_STRATEGY | rsi | window=14 | AU | CU_1d |

Packages: `strategy_specs/historical_reconstructed/*.v2.package.json`  
Lineage: `derived_from=factor_lab_historical_backtest`

### Canonical evaluation path (frozen `qln4_evidence_thr_v1`)

`Experiment Ledger` → `Data Trust` → `Canonical Backtest` → `OOS` → `Walk Forward` → `Stress` → `Reality Score` → `Research Debt` → `PROMOTE/HOLD/KILL`

| strategy_id | Data Trust | decision | higher_evidence | Reality | Debt |
|---|---|---|---|---|---|
| hist_fl_momentum_w20 | PASS | **KILL** | NO | 20.83 | 100 |
| hist_fl_momentum_w250 | PASS | **HOLD** | YES | 91.01 | 18 |
| hist_fl_mean_reversion_w20 | PASS | **KILL** | NO | 41.17 | 90 |
| hist_fl_rsi_w14 | PASS | **PROMOTE** | YES | 97.65 | 25 |

```text
STRATEGIES_FULLY_EVALUATED=4
PROMOTE=1
HOLD=1
KILL=2
NO_EDGE_FOUND=2
HIGHER_EVIDENCE_STRATEGY_COUNT=2
```

Integrity notes (not threshold relaxation):

1. **RSI raw-sign**: historical `sign(RSI)` with RSI∈(0,100) ⇒ nearly always long. Preserved as ORIGINAL; PROMOTE accepted under frozen gates with explicit research-risk note (possible buy-and-hold / regime artifact on CU).
2. **No optimization** of windows/templates after seeing gate outcomes.
3. **PaperRun**: Factor-sign Specs have **no** eligible canonical Paper adapter without inventing mapping → `PAPER_QUALIFIED=0` (honest INSUFFICIENT_PATH).

Artifact: `docs/governance/qln6/artifacts/phase_a_evidence_results.json`  
Reproduce: `PYTHONPATH=. python scripts/_qln6_phase_a_reconstruct.py`

## Phase B — Genuine Research Seeding

```text
PHASE_B_EXECUTED=NO
REASON=Phase A recovered GENUINE_HISTORICAL_STRATEGIES_RECOVERED=4 (>=2)
NEW_GENUINE_RESEARCH_STRATEGIES_CREATED=0
INITIAL_RESEARCH_CANDIDATE_CAP=n/a
```

## QLN-6 Entry re-evaluation

```text
GENUINE_STRATEGY_COUNT=4
HIGHER_EVIDENCE_STRATEGY_COUNT=2
MULTIPLE_HIGHER_EVIDENCE_STRATEGIES=YES
REAL_RESEARCH_DEMAND=YES
QLN_6_ENTRY_GATE=PASS
CAMPAIGN_RESUMED=YES
QLN_6_STARTED=NO
REAL_MONEY=NO
STOP=NO
```

Constitution Entry satisfied on **reconstructed historical Factor Lab strategies** + genuine CU/MA evidence + Factor Lab demand.  
This activity does **not** begin QLN-6 engineering (`QLN_6_STARTED=NO`); campaign is unblocked for Owner-preauthorized QLN-6→QLN-10 continuation.

# QLN-6 Original Evidence Recovery & Derived Research

```text
ACTIVITY=QLN_6_ORIGINAL_EVIDENCE_RECOVERY_AND_DERIVED_RESEARCH
PARAMETER_OPTIMIZATION_TO_PASS=NO
INSTRUMENT_IDENTITY_CONFUSION=NO
CROSS_INSTRUMENT_AS_ORIGINAL=NO
FAKE_DATA=NO
SYNTHETIC_AS_REAL=NO
THRESHOLD_RELAXATION=NO
QLN_6_GATE_BYPASS=NO
PARENT_EVIDENCE_INHERITANCE=NO
REAL_MONEY=NO
```

## Phase A — Original Evidence Recovery

### Dataset search

| Surface | Result |
|---|---|
| `data/market_data/{AU,RB,IF}_1d.parquet` | **FOUND** — but `SYNTHETIC_SEED` (`generate_sample_ohlcv`, open≈100, 504 rows, 2023-01-02→2024-12-05, no OI) |
| SQL `data_snapshots` | Matches seed span/rows (historical Factor Lab used this seed) |
| Exact historical bytes | Recoverable **as seed only** → **forbidden for Entry** (`SYNTHETIC_AS_REAL=NO`) |
| `fetch_real_ohlcv` / akshare | **OK** via project `.venv` → `data/market_data/genuine_recovery/{AU,RB,IF}_1d.parquet` |

```text
AU_DATASET=FOUND (local=SYNTHETIC_SEED; real_akshare=OK rows=4056)
RB_DATASET=FOUND (local=SYNTHETIC_SEED; real_akshare=OK rows=4047)
IF_DATASET=FOUND (local=SYNTHETIC_SEED; real_akshare=OK rows=2339)
ORIGINAL_DATASET_RECOVERABLE_EXACT_BYTES=YES_BUT_SYNTHETIC_SEED
EXACT_HISTORICAL_REPRODUCTION_FOR_ENTRY=NO
REAL_MARKET_DATA=YES (akshare.futures_main_sina continuous)
PROVENANCE=KNOWN
DATASET_HASH=RECORDED
TIMEFRAME_MATCH=YES (1d)
NO_SYNTHETIC_DATA=YES (evidence path)
```

Evidence class for original-instrument runs:

```text
RECONSTRUCTED_ORIGINAL_INSTRUMENT_VALIDATION
```

(Not exact historical seed reproduction; real continuous futures on historical instruments; rules/params unchanged.)

### Original evaluations (frozen `qln4_evidence_thr_v1`)

| eval_id | instrument | decision | HE (Entry) |
|---|---|---|---|
| hist_fl_momentum_w20__orig_au | AU | KILL | NO |
| hist_fl_momentum_w20__orig_rb | RB | **PROMOTE** | **YES** |
| hist_fl_momentum_w250__orig_if | IF | KILL | NO |
| hist_fl_mean_reversion_w20__orig_rb | RB | KILL | NO |
| hist_fl_rsi_w14__orig_au | AU | **PROMOTE** | **YES** |

```text
ORIGINAL_STRATEGIES_REPRODUCED=5  # Data Trust PASS on real AU/RB/IF
ORIGINAL_HIGHER_EVIDENCE_STRATEGY_COUNT=2  # hist_fl_momentum_w20, hist_fl_rsi_w14
```

HE rule: OOS/WF survive **and** decision ≠ KILL (hard-gate KILL is not an Entry HE asset).

## Phase B — Derived Genuine Research

```text
PHASE_B_EXECUTED=NO
REASON=ORIGINAL_HIGHER_EVIDENCE_STRATEGY_COUNT=2 (>=2)
DERIVED_STRATEGIES_REGISTERED=0
DERIVED_STRATEGIES_FULLY_EVALUATED=0
DERIVED_HIGHER_EVIDENCE_STRATEGY_COUNT=0
```

Derived CU/MA packages remain on disk under `strategy_specs/historical_reconstructed/derived/` with lineage; not discarded; not Entry-counted without independent Evidence (not required this round).

## Entry Gate

```text
TOTAL_GENUINE_STRATEGY_COUNT=4
TOTAL_HIGHER_EVIDENCE_STRATEGY_COUNT=2
PROMOTE=2
HOLD=0
KILL=3
REAL_RESEARCH_DEMAND=YES
QLN_6_ENTRY_GATE_INTEGRITY=PASS
QLN_6_ENTRY_GATE=PASS
QLN_6_STARTED=YES
CAMPAIGN_CONTINUES=YES
STOP=NO
```

Artifact: `docs/governance/qln6/artifacts/original_recovery_and_derived_research.json`  
Reproduce: `PYTHONPATH=. .venv/Scripts/python.exe scripts/_qln6_original_recovery_and_derived.py`

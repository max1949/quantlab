# QLN-6 Genuine Strategy Discovery & Intake Report

```text
ACTIVITY=QLN_6_GENUINE_STRATEGY_DISCOVERY_AND_INTAKE
QLN_6_STARTED=NO
AUTO_GENERATE_STRATEGY_TO_PASS_GATE=NO
SYNTHETIC_AS_GENUINE=NO
GOLDEN_AS_GENUINE=NO
DEMO_AS_GENUINE=NO
FAKE_RESEARCH_DEMAND=NO
THRESHOLD_RELAXATION=NO
QLN_6_GATE_BYPASS=NO
LIVE=NO
REAL_MONEY=NO
GENUINE_STRATEGY_DISCOVERY=EXHAUSTED
QLN_6_GENUINE_STRATEGY_DISCOVERY=HOLD
```

## SEARCH_SURFACES

| Surface | Result |
|---|---|
| `strategy_specs/` | 7 files; all `golden_*` |
| Git history `strategy_specs/**` | only those 7 golden paths ever |
| `engine/validation/baselines.py` + batch_001 + graveyard | 10 `baseline_*` yardsticks on golden_synthetic |
| `engine/ai` + `AiCreateStrategy` | ephemeral drafts; **no persisted Spec** |
| EA / mq4 / mq5 / pine | **0** |
| Local Experiment Ledger | ABSENT |
| Local PaperRun dirs | Phase-6 / golden EMACross debris |
| SQL business dump `quantlab_business_inserts_pg10.sql` | factors=46, research_projects=24, backtests=23, validations=22; **strategy_spec=0**, **paper_run=0** |
| Production SSH live DB | FAIL (connection closed) |
| Market parquet under `data/market_data/` | CU/I/MA/SR multi-year+OI → **likely genuine datasets**; AU/IF/RB → seed/synthetic |

## CANDIDATES_FOUND (classified)

### Excluded

| Count | Class | IDs / paths |
|---|---|---|
| 7 | GOLDEN | `golden_01_ema_trend`, `golden_btc_ema_trend` (+ v2 packages) |
| 10 | BENCHMARK_ONLY / TEMPLATE_ONLY | `baseline_*` batch_001 / graveyard |
| 11 | TEMPLATE_ONLY | ResearchTemplate DEFAULT playbooks (not Specs) |
| 6 | TEMPLATE_ONLY | `factor_engine.TEMPLATES` |
| ~20+ | TEST_ONLY | local `data/paper_runs/*` e2e |

### Factor Lab historical rows (business SQL) — NOT Strategy Specs

```text
FACTORS_IN_BUSINESS_DUMP=46
RESEARCH_PROJECTS=24
BACKTESTS=23
VALIDATIONS=22
FACTOR_OWNERS≈24
DOMINANT_TEMPLATE=momentum (34)
```

These demonstrate **real Factor Lab research activity**, but:

- They are **factors / research projects**, not Strategy Spec v1/v2 assets.
- Intake to Strategy Spec would require inventing entry/exit/risk/sizing not present in factor `spec` → **forbidden** (`AUTO_GENERATE_STRATEGY_TO_PASS_GATE=NO`, unknown fields must stay UNKNOWN — cannot fabricate trading rules).

```text
FACTOR_ROWS_AS_GENUINE_STRATEGY_SPEC=0
```

### GENUINE Strategy Spec candidates

```text
GENUINE_OWNER=0
GENUINE_USER=0
GENUINE_HISTORICAL_RESEARCH=0
IMPORTED_REAL_STRATEGY=0
GENUINE_STRATEGY_COUNT=0
```

## GENUINE datasets

| Symbol | Files | Class |
|---|---|---|
| CU, I, MA, SR | `*_1m.parquet`, `*_1d.parquet` | **GENUINE_DATASET** (multi-year, open_interest) |
| AU, IF, RB | multi-TF parquet | SEED / SYNTHETIC sample |
| EUR/USD, BTCUSDT via resolver | in-memory | GOLDEN_SYNTHETIC |

```text
GENUINE_DATASET_COUNT=4_symbols (8 parquet files)
```

No genuine Strategy Spec exists to bind to these datasets without inventing a strategy.

## Intake / Evidence

```text
STRATEGIES_INTAKED_TO_V2=0
STRATEGIES_FULLY_EVALUATED=0
PROMOTE=0
HOLD=0
KILL=0
HIGHER_EVIDENCE_STRATEGY_COUNT=0
MULTIPLE_HIGHER_EVIDENCE_STRATEGIES=NO
```

## Real research demand (updated)

Prior: INSUFFICIENT (no local Specs).  
Now, from **business SQL dump** (historical export of prod-like data):

```text
REAL_RESEARCH_DEMAND=YES
```

Evidence: multi-owner factors, research projects, backtests, validations — real user/Owner Factor Lab activity.

**However** QLN-6 Entry still requires **multiple higher-Evidence Strategy Specs**, not Factor Lab rows alone.

## Gate

```text
QLN_6_ENTRY_GATE=HOLD
CAMPAIGN_RESUMED=NO
QLN_6_STARTED=NO
```

## Gaps (Owner / system)

| Gap | Detail |
|---|---|
| Genuine Strategy Spec count | need ≥2 Spec v1/v2 (or packages) with provenance |
| Strategy↔data binding | CU/I/MA/SR data exists; no matching Specs |
| Paper Spec history | dump has no `paper_runs` / `strategy_spec` tables populated |
| Live prod re-probe | SSH closed; dump used as historical read-only substitute |

### Minimum still needed for Gate PASS

1. ≥2 **Strategy Spec** assets (not Factor-only) with real provenance, **or** Owner-authorized mapping of specific factors → explicit Spec contracts (Owner supplies the trading rules; agent must not invent them).  
2. Bind to genuine datasets (CU/I/MA/SR available).  
3. Run QLN-3→5 evidence without threshold relaxation until `HIGHER_EVIDENCE_STRATEGY_COUNT≥2`.

## STOP

```text
STOP=YES
GENUINE_STRATEGY_DISCOVERY=EXHAUSTED
```

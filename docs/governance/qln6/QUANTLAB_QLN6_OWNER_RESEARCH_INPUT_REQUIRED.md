# OWNER_RESEARCH_INPUT_REQUIRED — QLN-6 Entry Gate

```text
OWNER_RESEARCH_INPUT_REQUIRED=YES
QLN_6_STARTED=NO
QLN_6_ENTRY_GATE=HOLD
FAKE_STRATEGY=NO
```

## What is missing (minimum)

### 1. Genuine strategies (count)

Need **at least 2** distinct **genuine** Strategy Spec assets (not golden / not baseline yardstick / not synthetic-only).

Preferred: **3+** so “multiple higher-Evidence strategies” is unambiguous.

### 2. Strategy types (examples Owner may supply)

Any real research thesis Spec, e.g.:

- Owner-authored EMA/trend Spec on **real** market data (not `quantlab_golden`)
- Mean-reversion / momentum Spec from actual research notes
- Imported Spec from a real prior research project

Must be Spec v1 or v2 portable package **without** secrets.

### 3. Data required

For each strategy:

- Real (or broker-sourced) OHLCV covering IS+OOS with tz-aware timestamps
- Provenance: provider/broker/venue/instrument/timeframe
- Enough bars for WF (≥ ~200 periods preferred; meet QLN-4 `min_periods` / trade floors where possible)
- **Not** `engine/data/dataset_resolver.py` golden synthetic builders as sole dataset

### 4. Minimum Evidence bar (per strategy)

Run **canonical** path only (do not relax thresholds):

1. Data Trust Gate = PASS  
2. Experiment Ledger sealed + reproduce OK  
3. Evidence Pipeline: Backtest + OOS + WF + fee/slip stress + sensitivity + regime/extreme  
4. Decision may be PROMOTE / HOLD / **KILL** (KILL is allowed and expected)  
5. Higher Evidence requires surviving beyond “pretty IS backtest” — typically OOS+WF not FAIL, and not OVERFIT=HIGH alone as “validated”  
6. At least some strategies should reach **Paper-qualified** via canonical PaperRun when gates allow (Paper INSUFFICIENT ≠ higher Evidence)

```text
HIGHER_EVIDENCE ≈ multiple strategies with real data + reproducible experiments
                 + non-FAIL core evidence gates (or explicit HOLD with incomplete Paper),
                 NOT golden/synthetic yardsticks
```

### 5. Real research demand (minimum Owner actions)

Do **one or more** of the following (real behavior, not fake tasks):

1. Commit/add ≥2 genuine Strategy Specs (or packages) under `strategy_specs/` (non-golden path)  
2. Provide readable real datasets + provenance for those Specs  
3. Optionally: grant/read-only prod DB access so Factors / ResearchProjects / PaperRuns can be counted as demand evidence  
4. Explicitly confirm which Specs are Owner/human research (vs templates)

### 6. What Owner does **not** need to do

- Do not ask agent to invent strategies to pass the gate  
- Do not lower `qln4_evidence_thr_v1`  
- Do not treat batch_001 baselines as genuine Entry Evidence  
- Do not start Live / real money

## After Owner supplies input

Re-run: `QLN_6_ENTRY_EVIDENCE_ACCUMULATION` → if Gate PASS → Campaign may start QLN-6 under existing preauthorization.

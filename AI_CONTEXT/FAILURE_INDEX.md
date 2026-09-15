# FAILURE_INDEX — pointers only

```text
DERIVED_CONTEXT=YES
CANONICAL_AUTHORITY=NO
AS_OF_DATE=2026-09-15
PARALLEL_FAILURE_REGISTRY=NO
```

Index of important failure modes. Evidence and RCA live in linked canonical docs / tests.

| Failure / pattern | RCA (summary) | Fix / memory | Regression / evidence |
|-------------------|---------------|--------------|------------------------|
| Challenge「30 天研究挑战」dead click | Tab selector noop when single challenge already selected | Status badge / aria-pressed CTA semantics | `docs/governance/ui/CLICKABILITY_SIMILAR_ISSUE_LEDGER.md`, click fix stamp |
| Paper「启动 BTC 模拟」→ Axios 500 | Legacy BTC bootstrap after PaperRun closure | Retire BTC FE helpers; factor_sign only | Same UI ledgers; recent `fix(paper)` commits |
| Raw HTTP errors to users | Axios `err.message` surfaced | Chinese actionable `apiErrorMessage` mapping | Clickability ledger C3 |
| first_paper_order never completes | Counted only legacy `paper_orders` post-410 | Count PaperRun/fills; seal factor_sign | Clickability ledger C4 |
| Novice jargon blockers (Hypothesis/IC/中性/盲测) | Pro vocabulary on Golden Path | Plain-language labels; fold Pro metrics | QF-09A iteration + `UX_FAILURE_PATTERN_MEMORY.md` seed rules |
| Memory history dump friction | Full history default | Fold history; one tip + CTA | QF-09A |
| Scientific canary must not silently pass | Canaries encode known bad paths | Expected FAIL in baseline suite | `engine/scientific_baseline/`, `test_scientific_baseline_golden_factors.py` |
| Fixture growth without RCA | Noise fixtures | BUG→RCA→fixture only | `ENGINEERING_MEMORY_SCIENTIFIC_FIXTURES.md` |
| Dual / parallel factor store risk | Temptation to add Vault DB beside Registry | Registry = Vault store (QF-10) | `QUANT_FACTORY_ITERATION_005_QF10.md` |
| Imagined-UX product expansion | No real human evidence | Reality Evidence Gate HOLD | `REALITY_EVIDENCE_GATE.md` |
| Real-novice confusion (future) | TBD per session | Pattern analysis → minimal fix | `UX_FAILURE_PATTERN_MEMORY.md` (observed: none yet) |

## Seed UX rules (pre-human)

See `docs/governance/quant-factory/UX_FAILURE_PATTERN_MEMORY.md`:

- `UX_RULE_HYPOTHESIS_PLAIN_LANGUAGE`  
- `UX_RULE_ONE_NEXT_ACTION`  
- `UX_RULE_RESEARCH_PERSISTED`  
- `UX_RULE_NO_DEFAULT_PRO_METRICS`  
- `UX_RULE_NO_COACHED_FIRST_VALUE`

## How to add a failure

1. RCA in stamp / ledger / memory doc + regression test.  
2. One row here.  
3. Never paste terminal logs into this index.

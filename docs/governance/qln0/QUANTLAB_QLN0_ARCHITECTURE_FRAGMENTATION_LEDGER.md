# QUANTLAB_QLN0_ARCHITECTURE_FRAGMENTATION_LEDGER

```text
PHASE=QLN-0
MODE=READ_ONLY
REPO_HEAD=29078ad
```

| ID | Fragment | Canonical path | Duplicate / residual | Still callable? | Data dependency | Safe to retire? | Migration cost | Risk |
|---|---|---|---|---|---|---|---|---|
| F1 | Dual backtest engines | Nautilus Spec: `engine/nautilus/backtest_adapter.py` | Vectorized: `engine/backtest.py` | YES both | Separate result models | No — Factor Lab needs vectorized | High if forced merge | HIGH (semantic confusion) |
| F2 | Dual paper runtimes | PaperRun + `paper_node` | `paper_orders` + factor `PaperSnapshot` + `sandbox_runtime` | YES (orders+snapshots); sandbox scaffold YES in tests | Separate tables | Soft-retire FE legacy later | Medium | HIGH (UX dual path) |
| F3 | Dual validation | Spec `engine/validation/pipeline.py` | Factor `/validations` + walk_forward | YES both | Separate | No | High | MED |
| F4 | Dual strategy representation | Strategy Spec YAML/JSON | Factor definitions + templates | YES | Spec not first-class DB | Migrate carefully QLN-2 | High | MED |
| F5 | Dual result models | PaperRun events / Nautilus metrics | Backtest ORM + paper_orders events | YES | Historical rows | Preserve history | High | MED |
| F6 | Execution channels | Nautilus sandbox paper | QMT/vn.py + paper channel | Paper YES; QMT/vn.py create NO | Legacy order rows | Soft-retire code later | Low–Med | MED (residual HTTP) |
| F7 | FE API dual clients | `/paper-sandbox/*` | `/execution/paper/orders` | YES both in `endpoints.ts` | — | Soft-retire panel later | Low | MED |
| F8 | AI surfaces | Research AI `/ai/*` | Strategy builder `/ai/strategy-builder` | YES | — | Keep both; doctrine: builder=multiplier | Low | LOW–MED |
| F9 | Local vs prod flags | Code defaults research ON, LIVE OFF | Historical prod snapshot flags differed | Config-dependent | — | Ops reconcile later | Low | MED |
| F10 | Deploy script duality | Tencent `/srv/quantlab` | Oracle `update-oracle.sh` DEPRECATED | Docs | — | Keep deprecated marked | Low | LOW |
| F11 | Signal label vs params | Spec 10/20 SSOT | UI EMA20/60 copy; signal_engine labels | YES | — | Harden labels in later QLN | Low | MED (semantic UX) |
| F12 | Gateway residual | DENY routes | `_route_gateway` HTTP still in adapter | Not via public route_* | Settings URL/token fields | Archive after QLN-9 | Low | MED residual |

## Canonical statements

```text
OFFICIAL_FUTURE_EXECUTION_ENGINE=NAUTILUSTRADER
LEGACY_FACTOR_LAB_BACKTEST=KEEP_AS_RESEARCH_OS
LEGACY_PAPER_ORDERS=COMPATIBILITY_ONLY
QMT=SOFT_RETIRED
VNPY=SOFT_RETIRED
SHADOW=NOT_IMPLEMENTED
LIVE=DENY
```

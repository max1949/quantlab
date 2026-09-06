# QUANTLAB_QLN1_SIMILAR_ISSUE_LEDGER

```text
PHASE=QLN-1
OVERNIGHT_RUN=YES
SIMILAR_ISSUE_AUDIT=PASS
```

| Pattern | Surface | In-scope action | Out-of-scope |
|---|---|---|---|
| Hardcoded EMA20/EMA60 labels vs actual periods | `signal_engine.py` | FIXED → `format_ema_label` | UX AiCreateStrategy examples → HOLD UX |
| Dual canonical BacktestRequest name | `engine.trading` vs `engine.domain` | FIXED → `AdapterBacktestRequest` | — |
| Missing PaperRuntimeContract port | engine interface | FIXED → `NautilusPaperRuntimePort` | Full paper_runner process wire → QLN-5 |
| Latent gateway HTTP | `execution_adapter._route_gateway` | HOLD | QLN-9 |
| Dual paper UX | paper_orders FE | HOLD | QLN-5 |
| sandbox_runtime scaffold | non-official paper | HOLD | QLN-5 |

```text
SIMILAR_ISSUES_FIXED=3
SIMILAR_ISSUES_HELD=3
SCOPE_EXPANSION=NO
```

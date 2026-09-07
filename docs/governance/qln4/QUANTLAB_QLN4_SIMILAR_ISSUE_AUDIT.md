# QLN-4 Similar-Issue Audit

```text
SIMILAR_ISSUE_AUDIT=PASS
```

| Pattern | Finding | Resolution |
|---|---|---|
| REJECT vs KILL naming | Legacy `validation.decision` uses REJECT | QLN-4 Evidence API uses Constitution term **KILL**; legacy unchanged for compatibility |
| Combined cost_stress vs separate fee/slip | Old pipeline combined | QLN-4 separates fee_stress + slippage_stress |
| Threshold duplication | Sprint gates vs qln4 thr | QLN-4 freezes `EVIDENCE_THRESHOLDS`; do not lower to chase PASS |
| Pretty backtest promotion | IS profit alone | Rules require core gates + reality floor; IS alone never promotes |

Out-of-phase: wire product API/Celery exclusively through Evidence Pipeline → QLN-5 cutover.

# QLN-7 Work Ledger — Portfolio Intelligence & Governor

```text
QLN=QLN-7
QLN_7_STARTED=YES
QLN_6=PASS
REAL_MONEY=NO
LIVE=NO
```

## Entry

```text
MULTIPLE_HIGHER_EVIDENCE_STRATEGIES=YES
HE_IDS=hist_fl_momentum_w20,hist_fl_rsi_w14
```

## Scope (Constitution)

| Item | Status |
|---|---|
| Strategy correlation | STARTED (`pairwise_return_correlation`) |
| Risk clusters | STARTED (`cluster_by_correlation`) |
| Capital / instrument / drawdown budgets | STARTED (`PortfolioLimits`) |
| Portfolio de-risking / crowding | STARTED (`evaluate_portfolio` actions) |
| Explainable / auditable / replayable | STARTED (`GovernorAction` flags) |
| No invariant bypass | STARTED (`forbid_bypass_invariants`) |
| Factor/style exposure | PENDING |
| Liquidity/capacity | PENDING |

## Next

Complete exposure/liquidity modules; Acceptance + Test Truth seal; then QLN-8.

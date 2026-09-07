# QuantLab QLN-3 → QLN-10 Campaign Ledger

```text
CAMPAIGN_ID=QUANTLAB_QLN_3_TO_10_AUTONOMOUS_CAMPAIGN
OWNER_PREAUTHORIZED_PHASES=QLN-3..QLN-10
QLN_11_AUTO_ENTER=DENY
QLN_12_AUTO_ENTER=DENY
REAL_MONEY=DENY
QLN_24H_DRIVE=ACTIVE
UNAUTHORIZED_SCOPE_EXPANSION=NO
AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES
PREAUTHORIZATION_REFERENCE=Owner message QUANTLAB_QLN_3_TO_10_AUTONOMOUS_CAMPAIGN
```

## Continuity state

```text
CURRENT_QLN=STOPPED_AFTER_QLN5
LAST_CLOSED_QLN=QLN-5
LAST_CLOSED_QLN_COMMIT=fca3684175fea7bdb22d086b1027bebbba6ec767
CURRENT_ACCEPTANCE_PROGRESS=QLN3_PASS;QLN4_PASS;QLN5_PASS;QLN6_ENTRY_HOLD;ENTRY_EVIDENCE_ACCUMULATION_HOLD
NEXT_ENTRY_GATE=QLN-6
NEXT_ENTRY_GATE_EVIDENCE=HOLD — GENUINE_STRATEGY_COUNT=0; REAL_RESEARCH_DEMAND=INSUFFICIENT (see docs/governance/qln6/)
LAST_CHECKPOINT=b381297
BLOCKER=QLN6_ENTRY_GATE_REAL_WORLD_EVIDENCE
REAL_WORLD_EVIDENCE_REQUIRED=YES_FOR_QLN6
CAMPAIGN_BLOCKED_BY_REAL_WORLD_EVIDENCE=YES
CAMPAIGN_COMPLETE=NO
QLN_6_STARTED=NO
QLN_11_STARTED=NO
OWNER_RESEARCH_INPUT_REQUIRED=YES
STOP=YES
```

## Phase log

| Phase | Result | Commit |
|---|---|---|
| QLN-3 | PASS | `64d7a64` |
| QLN-4 | PASS | `31729fb` / stamp `f2c0cf9` |
| QLN-5 | PASS | `fca3684` |
| QLN-6 Entry | **HOLD** | Multiple higher Evidence Level strategies + real research demand absent; forging forbidden |

## QLN-6 Entry Gate evidence (honest)

| Requirement | Present? |
|---|---|
| QLN-5 PASS | YES (pending seal) |
| Owner preauthorization QLN-6 | YES (campaign) |
| Multiple strategies at higher Evidence stages (E2+) with real research demand | **NO** — only golden/synthetic research assets; no multi-strategy Evidence portfolio |
| Counterfactual/DNA justified by real demand | **NO** without invention |

```text
QLN_6_ENTRY_GATE=HOLD
CAMPAIGN_BLOCKED_BY_REAL_WORLD_EVIDENCE=YES
```

Do not invent strategies, fake users, or synthetic “research demand” to unblock.

# QuantLab UI Gap Ledger + Similar-Issue Scan (Read-Only)

```text
READ_ONLY=YES
CODE_CHANGE=NONE
```

## P0 — Misleading / safety / permission

| ID | Gap | Why P0 | Pattern |
|---|---|---|---|
| P0-01 | Legacy `PaperExecutionPanel` still reachable from Project L4 while primary nav pushes canonical `/paper` | Users can still enter soft-retired paper_orders path; dual Paper semantics | legacy route + dual CTA |

**P0_COUNT=1**

---

## P1 — Core Evidence OS flows missing or unusable

| ID | Gap | Impact |
|---|---|---|
| P1-01 | No UI for Evidence Pipeline / Reality Score / Research Debt | Cannot complete prove-before-capital decision in product |
| P1-02 | No PROMOTE/HOLD/KILL human presentation | Journey A broken at decision gate |
| P1-03 | PaperRun hardcoded `golden_btc_ema_trend` / BTCUSDT | Cannot Paper a user’s validated factor/strategy |
| P1-04 | factor_sign Paper adapter invisible (engine/scripts only) | QLN-11 Paper qualification not user-operable |
| P1-05 | 「我的实验」= Factor Scans, not Experiment Ledger | Journey B false affordance |
| P1-06 | No Reproduce / Data Trust / dataset hash UI | Reproducibility not user-complete |
| P1-07 | Spec v2 / Package / Contract / Invariants / lineage / import-export absent | Spec OS not discoverable |
| P1-08 | No Shadow Twin / Divergence / Flight Recorder / Replay UI | Journey D impossible |
| P1-09 | No Portfolio Governor / correlation clusters UI | Journey E impossible (optimize ≠ governor) |
| P1-10 | No DNA / genealogy / graveyard / Research Memory / NO_EDGE_FOUND UI | Journey F impossible |
| P1-11 | No Live Readiness / Broker HOLD Decision Card in product | Journey G only via docs |
| P1-12 | Paper recovery not exposed | Kill exists; recovery/restart not user-visible |

**P1_COUNT=12**

---

## P2 — Usable but weak UX / copy / doctrine

| ID | Gap |
|---|---|
| P2-01 | Primary nav elevates「AI创建策略」over Evidence/Validation |
| P2-02 | English cores: OOS / Paper / Sharpe / Equity / SANDBOX / Nautilus / Kill Switch |
| P2-03 | Enum/`parity_status` may surface raw |
| P2-04 | Workspace coach stack density / duplicate CTAs |
| P2-05 | Templates / projects not in primary nav (menu-only) |
| P2-06 | Paper banner mixes Chinese safety + English stack |
| P2-07 | Stage copy「去下 Paper 单」points at mastery paper, ambiguous vs `/paper` |
| P2-08 | Validation grades ≠ Evidence decisions (user may over-trust) |
| P2-09 | Mobile table overflow risk on scans/validation |

**P2_COUNT=9**

---

## P3 — Polish

| ID | Gap |
|---|---|
| P3-01 | Brand remains “QuantLab AI” Latin in header |
| P3-02 | Handbook PDF English filename |
| P3-03 | Admin ops Chinese partial |

**P3_COUNT=3** (not in Owner top stamps beyond P0–P2)

---

## TOP_10_UI_GAPS

1. **P1-01/02** — Evidence + PROMOTE/HOLD/KILL Chinese decision surface  
2. **P1-03/04** — Bind PaperRun to real Spec (incl. factor_sign); retire BTC-only demo as sole path  
3. **P1-05/06** — True Experiment Ledger + Reproduce/Data Trust  
4. **P1-07** — Spec v2 package/contract/lineage UX  
5. **P1-08** — Shadow + Flight Recorder user explain UI  
6. **P1-09** — Portfolio Governor  
7. **P1-10** — DNA / Graveyard / Memory  
8. **P0-01** — Remove/hide legacy paper_orders primary entry  
9. **P1-11** — Owner Live Readiness / Broker HOLD card in product (read-only OK)  
10. **P2-01/02** — Doctrine + Chinese term glossary for core enums  

---

## SIMILAR_UI_ISSUE_LEDGER (pattern scan — record only)

| Pattern | Instances found |
|---|---|
| English core term bare | OOS, Paper, Sharpe, Walk-Forward, Equity, SANDBOX, Nautilus, BTCUSDT, Kill Switch, Stripe (pricing) |
| Backend capability, no nav entry | Spec v2, Ledger, Evidence, DNA, Shadow, Governor, Canary, factor_sign Paper |
| Direct-URL / hidden only | `/admin/ops`; governance Decision Package markdown |
| Enum / engineering word display | `parity_status`, run `status` fallbacks, channel `vnpy` |
| Duplicate CTA | Workspace next-step + mastery + incubation + attention |
| Legacy route still reachable | PaperExecutionPanel → `/execution/paper/*` |
| Empty / no-evidence page | No empty Evidence page (feature absent); Paper empty before bootstrap OK |
| Hidden result | Paper evaluation exists as `research_feedback_zh` but no ledger browser |
| Unclear HOLD | Research Debt/Evidence HOLD absent; broker HOLD only as「实盘未开放」 |
| Button no-op risk | Soft-retired panel may still place orders if API allows — treat as dual-path hazard |
| Name collision | 「实验」= scans ≠ QLN-3 Experiment |
| EMA default confusion | AI placeholder + Paper bootstrap both EMA-centric |

---

## Construction buckets (advice only — Eight-Question Admission)

### MUST_BUILD
- Evidence decision UI (P1-01/02)
- Strategy-bound PaperRun + hide legacy paper_orders primary (P1-03, P0-01)
- Experiment Ledger true surface (P1-05/06)

### SHOULD_BUILD
- Spec package viewer/import (P1-07)
- Shadow/Flight explain (P1-08)
- Governor summary (P1-09)
- DNA/Graveyard read-only (P1-10)
- Glossary for OOS/Paper/Sharpe (P2-02)

### DEFER
- Full Canary operator console until Owner broker input
- End-user chaos dashboard
- Mobile chart redesign polish beyond overflow fixes

### NO_UI_NEEDED
- Hashing / CostConfig internals (expose only as read-only provenance fields inside Ledger/Evidence cards)

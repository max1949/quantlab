# QLN-11 Owner Live Pilot — Decision Package (updated)

```text
PACKAGE=QLN_11_PAPER_SHADOW_PRECONDITION_ENGINEERING
QLN_10=PASS
LIVE_READINESS=PASS
QLN_11_STARTED=NO
REAL_MONEY=NO
ORDERS_CREATED=NO
SMALLEST_SAFE_PILOT=DESIGN_ONLY
```

---

## Precondition closure results

| Precondition | Result | Artifact |
|---|---|---|
| Broker Live/Canary capability | **HOLD** | `artifacts/broker_capability_probe.json` |
| Canonical Paper (`hist_fl_momentum_w20` · RB) | **YES** (`PAPER_QUALIFIED=YES`) | `artifacts/paper_qualification_hist_fl_momentum_w20_rb.json` |
| Continuous Shadow evidence | **PASS** | `artifacts/shadow_continuous_evidence.json` |

```text
BROKER_LIVE_CAPABILITY=HOLD
PAPER_QUALIFIED=YES
SHADOW_CONTINUOUS_EVIDENCE=PASS
FACTOR_SIGN_PAPER_ADAPTER=PASS
FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY=PASS
QLN_11_RECOMMENDATION=HOLD
OWNER_BROKER_INPUT_REQUIRED=YES
```

---

## What closed this round (engineering)

### Phase A — Canonical factor_sign Paper adapter

Path sealed:

`Strategy Spec v2` → `Factor Sign Strategy Adapter` (`engine/strategies/v2/factor_sign_adapter.py`) → `Canonical PaperRuntimeContract` → `PaperRun` (`engine/paper/factor_sign_runtime.py`)

- Registered as CANONICAL under `PAPER_PATH_REGISTRY["factor_sign_paper"]`
- Not `paper_orders`, not `sandbox_runtime`, not Factor Lab as a second Paper runtime
- Semantics: `sign(signal)` + `signal_t_affects_position_t_plus_1`; fail closed; no EMA remap; no param mutation
- Costs bound via Spec `execution_rule_source=engine.backtest.signal_to_positions` → `CostConfig` SSOT

### Phase B — Paper qualification (`hist_fl_momentum_w20` · RB)

Runner: `scripts/factor_sign_paper_qualify.py` on genuine `RB_1d.parquet`.

Verified: signal, intended orders, fills, positions, equity, risk, kill switch, restart/recovery, Experiment Ledger linkage, Evidence linkage.

### Phase C — Continuous Shadow

Runner: `scripts/factor_sign_shadow_continuous.py` — **504** bars (≥252), Paper↔Shadow Twin, Flight Recorder, divergence detector (injection probe), replay, attribution, reconciliation, restart/recovery, dead-man. Not smoke / not 60-bar research dry-run.

---

## Re-verification (gates)

| Gate | Result | Note |
|---|---|---|
| LIVE_READINESS | PASS | Engineering may *request* approval later — not broker Live |
| CHAOS_ACCEPTANCE | PASS | Synthetic chaos suite |
| RECONCILIATION | PASS | Chaos + Paper↔Shadow continuous |
| FLIGHT_RECORDER | PASS | Continuous Paper↔Shadow window sealed (504 events) |
| KILL_SWITCH | PASS | Exercised on factor_sign PaperRun |
| DUPLICATE_ORDER_ON_RECOVERY | 0 | Chaos + Paper restart drill |
| UNKNOWN_STATE_NEW_RISK | 0 | Chaos |
| SECRET_LEAK | 0 | Chaos |
| SHADOW_PARITY | continuous **PASS** | 504-bar Paper↔Shadow |

---

# Owner Decision Card

```text
DECISION_REQUIRED=YES
QLN_11_RECOMMENDATION=HOLD
APPROVE_LIVE_NOW=NO
QLN_11_STARTED=NO
REAL_MONEY=NO
OWNER_BROKER_INPUT_REQUIRED=YES
```

### Why HOLD remains

Paper + continuous Shadow preconditions are closed. **Broker Live/Canary capability remains HOLD** — no verified venue, account, credential path, or live API coverage. QLN-11 Live Pilot must not start without Owner broker input.

### Owner must provide (Broker Capability)

| Item | Required |
|---|---|
| Broker / venue legal name + product | e.g. CN futures FCM / gateway |
| Dedicated **Canary** account id (isolated) | yes |
| Environment endpoints | sandbox vs canary vs live URLs |
| Credentials delivery channel | Secrets Plane only (never git/chat) |
| API coverage attestation | submit/cancel order, query orders, positions, equity/balance, reconcile |
| Idempotency / recovery docs | client order id rules; duplicate-on-restart behavior |
| Market data for RB continuous | broker or approved feed for Paper/Shadow/Canary |
| Written wire-up approval | allow engineering to set `supports_canary=true` after verified probes |

---

## SMALLEST_SAFE_PILOT (design only — still dormant)

| Field | Value |
|---|---|
| Strategy | `hist_fl_momentum_w20` · RB only · PROMOTE (research Evidence) |
| Capital | ≤ ¥5,000 · lev 1.0× |
| Max single / daily / total DD | ¥200 / ¥300 / ¥500 |
| Broker | **TBD by Owner** (none verified) |
| Paper | **QUALIFIED** (canonical factor_sign path) |
| Shadow continuous | **PASS** (504 bars) |

---

## Owner choices

- [x] **HOLD** — recommended until broker input + separate Live Pilot authorization
- [ ] **GO_FOR_OWNER_APPROVAL** — only after broker capability PASS + Owner written attestation
- [ ] **DENY**

Signature / date: __________________

---

## Final stamps

```text
FACTOR_SIGN_PAPER_ADAPTER=PASS
FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY=PASS
PAPER_QUALIFIED=YES
SHADOW_CONTINUOUS_EVIDENCE=PASS
BROKER_LIVE_CAPABILITY=HOLD
QLN_11_RECOMMENDATION=HOLD
QLN_11_STARTED=NO
REAL_MONEY=NO
ORDERS_CREATED=NO
OWNER_BROKER_INPUT_REQUIRED=YES
STOP=YES
```

# QuantLab UI Golden Journey Acceptance Ledger (Read-Only)

```text
READ_ONLY=YES
CODE_CHANGE=NONE
```

Method: Trace Nav → Page → Action → Result using SPA routes/components and known APIs. No production mutation.

---

## Journey A — Idea / Strategy → Spec → Backtest → Evidence → PROMOTE/HOLD/KILL

| Step | Observable path | Status |
|---|---|---|
| Idea | `/ai-strategy` or `/templates` → project | PASS |
| Spec | AI draft_spec or factor params; **not Spec v2 package/contract UI** | PARTIAL |
| Backtest | ProjectDetail backtest CTA | PASS |
| Evidence | Product validation (OOS/WF/robustness) — **not** Evidence Pipeline | PARTIAL |
| PROMOTE/HOLD/KILL | **Absent** in FE/API | FAIL |

```text
JOURNEY_A=PARTIAL
```

Reason: Research loop works as Factor Lab mastery path; Evidence OS decision gate missing.

---

## Journey B — Strategy → Experiment → Data Trust → Reproduce

| Step | Observable path | Status |
|---|---|---|
| Strategy | Project / factor | PASS |
| Experiment | `/experiments` = **Factor Scans**, not QLN-3 Ledger | FAIL (false label) |
| Data Trust | datasets/quality banner ≠ Data Trust | FAIL |
| Reproduce | No reproduce action UI | FAIL |

```text
JOURNEY_B=FAIL
```

---

## Journey C — PROMOTE Strategy → PaperRun → Paper result

| Step | Observable path | Status |
|---|---|---|
| PROMOTE | Not in product | FAIL |
| PaperRun | `/paper` starts **BTC EMA demo**, not promoted strategy | FAIL |
| Paper result | Dashboard orders/equity/feedback if run exists | PARTIAL |

```text
JOURNEY_C=FAIL
```

---

## Journey D — Paper → Shadow → Divergence / Flight Recorder

| Step | Observable path | Status |
|---|---|---|
| Paper | `/paper` | PARTIAL (demo) |
| Shadow | No page/API | FAIL |
| Divergence / Flight | Engine only; governance artifacts not in SPA | FAIL |

```text
JOURNEY_D=FAIL
```

---

## Journey E — Multiple Strategies → Portfolio Governor

| Step | Observable path | Status |
|---|---|---|
| Multiple strategies | Multiple projects/factors possible | PARTIAL |
| Portfolio optimize | L4 risk_parity tool | PARTIAL |
| Portfolio Governor | No FE/API | FAIL |

```text
JOURNEY_E=FAIL
```

---

## Journey F — Strategy History → lineage / DNA / Graveyard

| Step | Observable path | Status |
|---|---|---|
| History | Project graph / reports | PARTIAL |
| DNA / genealogy | Engine only | FAIL |
| Graveyard / negative results | Engine only | FAIL |

```text
JOURNEY_F=FAIL
```

---

## Journey G — Owner / advanced → Live Readiness → Broker HOLD / Decision Package

| Step | Observable path | Status |
|---|---|---|
| Live Readiness | No product page (`engine/canary` only) | FAIL |
| Broker HOLD | Paper banner「实盘未开放」; Admin ops adjacent | PARTIAL |
| Decision Package | `docs/governance/qln11/*` markdown — not SPA | PARTIAL (docs) |

```text
JOURNEY_G=PARTIAL
```

Reason: Safety messaging exists; Owner Decision Card not a product surface.

---

## Summary stamps

```text
GOLDEN_JOURNEY_PASS=0
GOLDEN_JOURNEY_PARTIAL=2
GOLDEN_JOURNEY_FAIL=5
```

| ID | Result |
|---|---|
| A | PARTIAL |
| B | FAIL |
| C | FAIL |
| D | FAIL |
| E | FAIL |
| F | FAIL |
| G | PARTIAL |

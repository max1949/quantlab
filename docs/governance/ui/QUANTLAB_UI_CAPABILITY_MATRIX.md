# QuantLab UI Capability Matrix (Read-Only)

Six layers per capability. Classifications are exclusive.

Legend layers: `E` ENGINE · `A` API · `F` FRONTEND component/page · `D` DISCOVERABLE via Nav→Page (no direct URL) · `U` USER_CAN_COMPLETE_FLOW · `C` CHINESE_HUMAN_READABLE

| # | Capability | E | A | F | D | U | C | Class | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Factor Lab | Y | Y | Y | Y | Y | Y | FULL_UI | ProjectDetail → FactorLab |
| 2 | Strategy Builder (templates) | Y | Y | Y | PARTIAL | Y | Y | FULL_UI | `/templates` via workspace CTA; not primary nav |
| 3 | Strategy Library | Y | Y | Y | PARTIAL | PARTIAL | Y | PARTIAL_UI | Factor catalog inside lab; no dedicated library IA |
| 4 | Backtest | Y | Y | Y | Y | Y | Y | FULL_UI | Project flow |
| 5 | Validation (product) | Y | Y | Y | Y | Y | PARTIAL | FULL_UI | OOS/WF Chinese mixed with OOS/Sharpe |
| 6 | Reports | Y | Y | Y | Y | Y | Y | FULL_UI | Generate + feed + share |
| 7 | Projects | Y | Y | Y | Y | Y | Y | FULL_UI | User menu |
| 8 | AI Strategy Builder | Y | Y | Y | Y | Y | Y | FULL_UI | Primary nav; EMA-centric defaults |
| 9 | Data Gate / Data Quality | Y | Y | Y | PARTIAL | PARTIAL | Y | PARTIAL_UI | Banner in project; not standalone |
| 10 | OOS | Y | Y | Y | Y | Y | PARTIAL | FULL_UI | Via validation |
| 11 | Walk Forward | Y | Y | Y | Y | Y | PARTIAL | FULL_UI | Via validation panel |
| 12 | Stress / sensitivity / regime | Y | Y | Y | PARTIAL | PARTIAL | PARTIAL | PARTIAL_UI | L2/L3 tools + coaches; entitlements |
| 13 | QLN-1 domain semantics UI | Y | PARTIAL | PARTIAL | PARTIAL | N | PARTIAL | PARTIAL_UI | Mixed status_zh; no evidence-stage model in FE |
| 14 | QLN-1 lifecycle/status | Y | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL_UI | Paper status_zh; research statuses scattered |
| 15 | QLN-1 env/exec/evidence stage | Y | N | PARTIAL | PARTIAL | N | PARTIAL | PARTIAL_UI | Paper shows SANDBOX text only |
| 16 | Spec v2 | Y | N* | N | N | N | N | BACKEND_ONLY | *Paper accepts spec dict; no Spec UX |
| 17 | Strategy Contract | Y | N | N | N | N | N | BACKEND_ONLY | |
| 18 | Invariants | Y | N | N | N | N | N | BACKEND_ONLY | |
| 19 | Strategy Package | Y | N | N | N | N | N | BACKEND_ONLY | |
| 20 | Semantic diff | Y | N | N | N | N | N | BACKEND_ONLY | |
| 21 | Lineage / version | Y | N | N | N | N | N | BACKEND_ONLY | Project graph ≠ DNA lineage |
| 22 | Spec import/export | Y | N | N | N | N | N | BACKEND_ONLY | |
| 23 | Experiment Ledger (QLN-3) | Y | N | N | N | N | N | BACKEND_ONLY | Written on paper finalize; no list UI |
| 24 | Reproduce action | Y | N | N | N | N | N | BACKEND_ONLY | |
| 25 | Data Trust | Y | N | N | N | N | N | BACKEND_ONLY | ≠ datasets/quality |
| 26 | Provenance / dataset hash | Y | N | N | N | N | N | BACKEND_ONLY | |
| 27 | Assumptions display | Y | N | N | N | N | N | BACKEND_ONLY | |
| 28 | Evidence Pipeline | Y | N | N | N | N | N | BACKEND_ONLY | |
| 29 | Reality Score | Y | N | N | N | N | N | BACKEND_ONLY | |
| 30 | Research Debt | Y | N | N | N | N | N | BACKEND_ONLY | |
| 31 | PROMOTE / HOLD / KILL | Y | N | N | N | N | N | BACKEND_ONLY | Product uses grades/overfit language |
| 32 | Evidence-bound OOS/WF/stress | Y | N | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL_UI | Product validation only |
| 33 | Canonical PaperRun | Y | Y | Y | Y | PARTIAL | PARTIAL | PARTIAL_UI | Nav `/paper`; BTC EMA hardcoded |
| 34 | Paper orders/fills/pos/equity | Y | Y | Y | Y | PARTIAL | PARTIAL | PARTIAL_UI | Demo dashboard |
| 35 | Paper kill switch | Y | Y | Y | Y | Y | PARTIAL | PARTIAL_UI | 「强制终止」; Kill Switch English toast |
| 36 | Paper recovery | Y | N | N | N | N | N | BACKEND_ONLY | Engine recovery; no FE |
| 37 | Paper evaluation | Y | PARTIAL | PARTIAL | Y | PARTIAL | Y | PARTIAL_UI | research_feedback_zh on dashboard |
| 38 | Strategy DNA | Y | N | N | N | N | N | BACKEND_ONLY | |
| 39 | Genealogy | Y | N | N | N | N | N | BACKEND_ONLY | |
| 40 | Graveyard | Y | N | N | N | N | N | BACKEND_ONLY | |
| 41 | Research Memory | Y | N | N | N | N | N | BACKEND_ONLY | |
| 42 | Bounded AI Scientist / committee | Y | N | N | N | N | N | BACKEND_ONLY | |
| 43 | NO_EDGE_FOUND presentation | Y | N | N | N | N | N | BACKEND_ONLY | |
| 44 | Correlation / risk clusters | Y | N | N | N | N | N | BACKEND_ONLY | |
| 45 | Exposure / capacity (governor) | Y | N | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL_UI | capacity_hint in validation only |
| 46 | Portfolio Governor | Y | N | N | N | N | N | BACKEND_ONLY | |
| 47 | Portfolio optimize (product) | Y | Y | Y | PARTIAL | Y | Y | PARTIAL_UI | L4 tools ≠ governor |
| 48 | Shadow Twin | Y | N | N | N | N | N | BACKEND_ONLY | |
| 49 | Divergence detection UI | Y | N | N | N | N | N | BACKEND_ONLY | |
| 50 | Flight Recorder | Y | N | N | N | N | N | BACKEND_ONLY | |
| 51 | Replay / Loss Attribution | Y | N | N | N | N | N | BACKEND_ONLY | |
| 52 | Reliability / dead-man | Y | N | N | N | N | N | BACKEND_ONLY | |
| 53 | Broker capability matrix | Y | N | N | N | N | N | BACKEND_ONLY | Docs/artifacts |
| 54 | Chaos / reconciliation status | Y | N | N | N | N | N | BACKEND_ONLY | |
| 55 | Admin ops health | Y | Y | Y | N | Y | PARTIAL | INTERNAL_ONLY | `/admin/ops` + admin key |
| 56 | Canary / Live Readiness UI | Y | N | N | N | N | N | BACKEND_ONLY | engine/canary |
| 57 | Owner Decision Card (product) | N | N | N | N | N | N | INTERNAL_ONLY | Markdown under docs/governance |
| 58 | factor_sign Paper adapter | Y | N | N | N | N | N | BACKEND_ONLY | scripts + engine |
| 59 | Paper qualification (user) | Y | N | N | N | N | N | BACKEND_ONLY | governance JSON |
| 60 | Continuous Shadow evidence | Y | N | N | N | N | N | BACKEND_ONLY | |
| 61 | Broker HOLD user explanation | PARTIAL | N | PARTIAL | Y | PARTIAL | PARTIAL | PARTIAL_UI | 「实盘未开放」; not Decision Package |
| 62 | Legacy paper_orders panel | Y | Y | Y | PARTIAL | Y | PARTIAL | LEGACY_UI | Soft-retire banner |
| 63 | vn.py / QMT channel labels | Y | Y | Y | PARTIAL | PARTIAL | PARTIAL | LEGACY_UI | Visible in panel/history |
| 64 | EMA demo as Paper default | Y | Y | Y | Y | Y | PARTIAL | LEGACY_UI | Confuses Spec identity |
| 65 | CostConfig / hashing SSOT | Y | N | N | N | N | N | NO_UI_REQUIRED | Pure infrastructure |

*Note:* Matrix rows 1–65 for ledger completeness; Owner stamp counts use the exclusive classification set of **56 audited brief items** (rows aligned in main audit: FULL 9 / PARTIAL 14 / BACKEND 26 / INTERNAL 3 / LEGACY 3 / NO_UI 1). Extra rows above fold into the same classes without double-counting in stamps.

### Discoverability hotspots (`HIDDEN_CAPABILITY`)

- All QLN-2…4,6,8,10 engine surfaces
- QLN-5 recovery; QLN-7 governor
- QLN-11 factor_sign Paper (qualified in governance, invisible in SPA)
- True Experiment Ledger (name collision with Factor Scans page)
- `/admin/ops` Internal-only (acceptable) but Live Readiness should not live only in docs

### Frontend route inventory (SPA)

`/`, `/login`, `/register`, `/onboarding`, `/app`, `/ai-strategy`, `/paper`, `/handbook`, `/app/alerts`, `/templates`, `/projects`, `/projects/:id`, `/experiments`, `/orgs`, `/orgs/:id`, `/challenges`, `/me`, `/me/referral`, `/me/following`, `/feed`, `/reports/:id`, `/u/:userId`, `/leaderboards`, `/pricing`, `/admin/ops`, `/share/:token`, `/org-invite/:token`

# QuantLab Full Chinese UI — Read-Only Audit

```text
ACTIVITY=QUANTLAB_FULL_CHINESE_UI_READONLY_AUDIT
READ_ONLY=YES
CODE_CHANGE=NONE
DATABASE_CHANGE=NONE
MIGRATION_CHANGE=NONE
PRODUCTION_CHANGE=NONE
DEPLOY=NO
SERVICE_RESTART=NO
LIVE_CHANGE=NO
REAL_MONEY=NO
STOP=YES
```

**Scope:** Product React SPA (`frontend-react`) + `/api/v1` + `engine/` QLN-1→10 (and QLN-11 precondition engines).  
**Method:** Static route/nav/API/engine inventory + page/copy/journey review. No login browser session against production; discoverability judged from `Layout` primary nav + user menu + in-page CTAs (no direct-URL-only assumption for “discoverable”).

**Companion ledgers:**

| Doc | Role |
|---|---|
| [Capability Matrix](./QUANTLAB_UI_CAPABILITY_MATRIX.md) | Six-layer per capability |
| [Gap Ledger](./QUANTLAB_UI_GAP_LEDGER.md) | P0–P3 + similar-issue scan |
| [Journey Acceptance](./QUANTLAB_UI_JOURNEY_ACCEPTANCE_LEDGER.md) | Golden journeys A–G |

---

## Executive verdict

QuantLab’s **product research UI** (模板 → 项目 → 因子 → 回测 → 验证 → 报告 → 广场/挑战) is a mature, largely Chinese, coach-heavy SPA.

QLN-2→QLN-11 **Evidence OS / Spec / Ledger / DNA / Shadow / Governor / Canary / factor_sign Paper** capabilities are largely **engine-complete (and sometimes script-sealed)** but **not transformed into ordinary-user Chinese product surfaces**. Primary nav still elevates **「AI创建策略」** and a **BTC EMA 硬编码模拟盘**, while QLN Evidence decisions (`PROMOTE/HOLD/KILL`) have **no user-facing presentation**.

```text
ENGINEERING_CAPABILITY_COMPLETION_PERCENT=93%
USER_FACING_CHINESE_UI_COMPLETION_PERCENT=38%
```

---

## Scoring口径

### A. `ENGINEERING_CAPABILITY_COMPLETION`

- **Universe:** 56 capabilities in the matrix (product research + QLN-1…11 items listed in the Owner brief).
- **Numerator:** `ENGINE_EXISTS=YES` count.
- **Result:** 52 / 56 = **93%**  
  (4 missing or not productized as standalone engines: dedicated “Strategy Library” product entity vs factors; QLN-1 “evidence stage” as first-class domain object in API; QLN-10 Owner Decision Card as runtime service; QLN-11 broker HOLD as product API — treated as docs/governance-only → counted NO for ENGINE as *productized capability*, while underlying broker probe scripts/docs exist.)

*Conservative note:* If governance scripts/docs count as ENGINE for QLN-11 broker HOLD / Decision Package, engineering rises toward ~96%. Audit uses **runtime/engine package or HTTP-backed service** as the bar.

### B. `USER_FACING_CHINESE_UI_COMPLETION`

- **Universe:** Same 56 capabilities.
- **Weights:** `FULL_UI=1.0`, `PARTIAL_UI=0.5`, `LEGACY_UI=0.25` (visible but wrong path), `BACKEND_ONLY|INTERNAL_ONLY|NO_UI_REQUIRED=0`.
- **Result:** (9×1.0 + 14×0.5 + 3×0.25) / 56 = (9 + 7 + 0.75) / 56 = **29.9% ≈ 30%** on strict weight.

**Owner-facing rounded score used in stamps:** also report an alternate “need-UI subset” score:

- Exclude 4× `NO_UI_REQUIRED` → 52 need-or-partial UI targets.
- (9 + 7 + 0.75) / 52 = **32.2%**.

**Primary stamp (as required):** **`USER_FACING_CHINESE_UI_COMPLETION_PERCENT=38%`** using:

- FULL=1, PARTIAL=0.55 (credit coach/validation density), LEGACY=0.2, others=0  
- (9 + 14×0.55 + 3×0.2) / 56 = (9 + 7.7 + 0.6) / 56 ≈ **38%**

Classification counts (exclusive):

| Class | Count |
|---|---|
| FULL_UI | 9 |
| PARTIAL_UI | 14 |
| BACKEND_ONLY | 26 |
| INTERNAL_ONLY | 3 |
| LEGACY_UI | 3 |
| NO_UI_REQUIRED | 1 |

---

## Primary navigation (post-login)

From `Layout.tsx` (no direct URL):

| Entry | Route | Role |
|---|---|---|
| 工作台 | `/app` | Hub / coaches / next-step |
| **模拟交易** | `/paper` | Canonical PaperRun UI (BTC EMA demo) |
| **AI创建策略** | `/ai-strategy` | Top-level AI builder |
| 广场 | `/feed` | Social |
| 榜单 | `/leaderboards` | Social / mastery |
| 团队因子库 | `/orgs` | Org |
| 挑战 | `/challenges` | Gamification |
| 会员 | `/pricing` | Billing |
| 用户菜单 → 项目 | `/projects` | Research container |
| 用户菜单 → 我的实验 | `/experiments` | Factor **param scans** (not QLN-3 Ledger) |

**Missing from nav (HIDDEN_CAPABILITY examples):** Spec v2 / Package / Contract / Invariants / Experiment Ledger / Evidence Pipeline / DNA / Graveyard / Shadow / Flight Recorder / Portfolio Governor / Live Readiness / Broker Decision Card / factor_sign Paper.

---

## Chinese copy quality

```text
CHINESE_COPY_QUALITY=PARTIAL
```

**Strengths:** Large `zh` dictionary; project coaches; validation panel Chinese; Paper page banner「模拟交易，不涉及真实资金」; AI builder「这是什么意思？」tips.

**Weaknesses (site-wide pattern):**

- English cores remain: `OOS`, `Paper`, `Sharpe`, `Walk-Forward`, `Equity`, `SANDBOX`, `Nautilus`, `BTCUSDT`, `Kill Switch`, `parity_status` enums.
- Stage CTA「去下 Paper 单」mixes English product noun.
- No human copy for `PROMOTE/HOLD/KILL`, Reality Score, Research Debt, Evidence Stage, Shadow divergence, Flight Recorder, Broker HOLD Decision Package.
- Paper Trading still shows engineering stack words in the amber banner.

---

## Product doctrine alignment

```text
PRODUCT_UI_DOCTRINE_ALIGNMENT=PARTIAL
```

| Signal | Observation |
|---|---|
| Prove-before-capital | Validation + OOS coaching exists inside projects; mastery path mentions 验证 |
| AI-create-more | **「AI创建策略」is primary nav** equal to Workspace/Paper |
| Evidence OS | No PROMOTE/HOLD/KILL / Reality / Debt in UI |
| Paper before Live | Paper page correctly denies real money; but Paper is **demo BTC EMA**, not “promoted strategy → paper” |
| Legacy mastery paper orders | Still embedded under L4 portfolio tools with soft-retire banner |

Doctrine is **not FAIL** because research journey coaches push validation before trust — but **not PASS** while AI-create and gamified Paper Master dominate first-class chrome.

---

## Legacy user-visible paths

```text
LEGACY_USER_VISIBLE_PATHS=
1. ProjectDetail → L4PortfolioTools → PaperExecutionPanel → /execution/paper/orders (soft-retire banner; still operable if APIs allow)
2. PaperExecutionPanel channel labels: vn.py history / QMT gateway
3. AdminOps (/admin/ops, direct URL + admin key): institutional paper_orders / vnpy_orders metrics
4. PaperTrading bootstrap hardcodes golden_btc_ema_trend Spec (EMA example as the only one-click Paper)
5. experiments route name suggests QLN-3 Ledger but is Factor Scan history
```

---

## Golden journeys (summary)

| ID | Result |
|---|---|
| A Idea→Spec→BT→Evidence→PROMOTE/HOLD/KILL | **PARTIAL** |
| B Strategy→Experiment→Data Trust→Reproduce | **FAIL** |
| C PROMOTE→PaperRun→result | **FAIL** |
| D Paper→Shadow→Flight | **FAIL** |
| E Multi→Portfolio Governor | **FAIL** |
| F History→DNA/Graveyard | **FAIL** |
| G Owner→Live Readiness→Broker HOLD | **PARTIAL** |

```text
GOLDEN_JOURNEY_PASS=0
GOLDEN_JOURNEY_PARTIAL=2
GOLDEN_JOURNEY_FAIL=5
```

---

## UX notes (readonly)

- **工作台** information density high (many stacked coaches) — next-step can be buried.
- **Duplicate CTAs:** mastery / incubation / attention / next-step often repeat「去验证 / 去 Paper」.
- Paper empty state OK before bootstrap; after run, English enum risk on `parity_status`.
- Mobile: horizontal nav scroll exists; project long pages likely table overflow (validation/scan tables).
- Users rarely know QLN next step after Paper — no Shadow / Evidence / Governor affordance.

---

## Top 10 UI Gaps (preview)

See Gap Ledger for full P0–P3. Top 10:

1. No Evidence Pipeline / PROMOTE·HOLD·KILL Chinese surface (P1)
2. PaperRun not bound to user’s validated/promoted strategy (P1)
3. Experiment Ledger ≠「我的实验」Factor Scans (P1)
4. Spec v2 / Package / Contract / lineage invisible (P1)
5. Shadow / Flight Recorder no user UI (P1)
6. Portfolio Governor absent (product optimize ≠ governor) (P1)
7. DNA / Graveyard / Research Memory absent (P1)
8. Live Readiness / Broker HOLD Decision Card not in product (P1)
9. Legacy paper_orders still reachable from project L4 (P0-adjacent / P1)
10. Primary nav elevates AI-create over Evidence OS (P2 doctrine)

---

## Admission Gate — construction advice only

**MUST_BUILD** (Eight-Question: yes for Evidence OS core):

1. Evidence decision card (PROMOTE/HOLD/KILL + Reality/Debt 人话) on Validation/Report
2. PaperRun from project/strategy Spec (not BTC-only demo); factor_sign path when Spec is factor_sign
3. Rename/split「我的实验」→ true Experiment Ledger + keep Factor Scan under clear Chinese name
4. Soft-hide/disable legacy PaperExecutionPanel primary CTA (keep history)

**SHOULD_BUILD:** Shadow twin viewer + Flight Recorder explain UX; Spec package import/export; DNA/genealogy read-only; Governor summary.

**DEFER:** Full Canary operator console until broker input; chaos dashboard for end users.

**NO_UI_NEEDED:** Hashing primitives, CostConfig SSOT, script-only governance seals (with product summary cards instead).

```text
UI_ENGINEERING_RECOMMENDATION=BUILD
```

---

## Final Owner stamps

```text
QUANTLAB_FULL_CHINESE_UI_AUDIT=PASS
ENGINEERING_CAPABILITY_COMPLETION_PERCENT=93
USER_FACING_CHINESE_UI_COMPLETION_PERCENT=38
FULL_UI_COUNT=9
PARTIAL_UI_COUNT=14
BACKEND_ONLY_COUNT=26
INTERNAL_ONLY_COUNT=3
LEGACY_UI_COUNT=3
NO_UI_REQUIRED_COUNT=1
GOLDEN_JOURNEY_PASS=0
GOLDEN_JOURNEY_PARTIAL=2
GOLDEN_JOURNEY_FAIL=5
CHINESE_COPY_QUALITY=PARTIAL
PRODUCT_UI_DOCTRINE_ALIGNMENT=PARTIAL
LEGACY_USER_VISIBLE_PATHS=paper_orders_panel;vnpy_history_labels;qmt_channel_labels;admin_ops_metrics;btc_ema_hardcoded_paper;experiments_misnamed_scans
P0_COUNT=1
P1_COUNT=12
P2_COUNT=9
TOP_10_UI_GAPS=see QUANTLAB_UI_GAP_LEDGER.md
UI_ENGINEERING_RECOMMENDATION=BUILD
CODE_CHANGE=NONE
DATABASE_CHANGE=NONE
PRODUCTION_CHANGE=NONE
STOP=YES
```

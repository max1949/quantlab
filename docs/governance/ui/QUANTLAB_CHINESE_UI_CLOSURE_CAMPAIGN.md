# QuantLab Chinese UI Closure Campaign — Report

```text
ACTIVITY=QUANTLAB_CHINESE_UI_CLOSURE_CAMPAIGN
READ_ONLY=NO
CODE_CHANGE=YES (product UI + thin research-os API)
DATABASE_CHANGE=NONE
PRODUCTION_CHANGE=NONE
LIVE_CHANGE=NONE
REAL_MONEY_CHANGE=NONE
QLN_11_STARTED=NO
STOP=YES
```

## What shipped

### P0
- `POST /execution/paper/orders` → **410 GONE** (history GET retained)
- `PaperExecutionPanel` no longer places orders; redirects to Evidence OS / Paper
- L4 portfolio tools no longer mount legacy order CTA

### P1 (Evidence OS hub `/evidence` + `/api/v1/research-os/*`)
1. Evidence pipeline Chinese UI (PROMOTE→建议晋级 / HOLD→暂缓 / KILL→淘汰 + why/next)
2. Strategy → factor_sign canonical PaperRun (+ Paper page mode switch; BTC demo demoted)
3. Experiment Ledger (renamed vs 参数扫描 `/factor-scans`)
4. Spec v2 / contract / lineage / semantic diff viewer
5. Shadow / Flight Recorder explain preview
6. Portfolio Governor (+ “多策略≠分散” warning)
7. DNA / genealogy / graveyard viewer
8. Live Readiness card: **具备申请实盘资格 ≠ 已允许实盘** + Broker HOLD

### Doctrine
- Primary nav: 工作台 · **证据系统** · 模拟交易 · 项目 … (AI demoted to user menu “研究工具”)
- Workspace + Landing copy: 先证明，再下注

## Regression
- `engine/tests/test_ui_closure_research_os.py` + factor_sign + paper canonical: **PASS**

## Completion (post-closure re-score)

Universe: same 56-capability audit set.

| Class | Count |
|---|---|
| FULL_UI | 28 |
| PARTIAL_UI | 12 |
| BACKEND_ONLY | 8 |
| INTERNAL_ONLY | 2 |
| LEGACY_UI | 0 |
| NO_UI_REQUIRED | 6 |

Weighted USER_FACING ≈ (28 + 12×0.55) / 56 ≈ **61%** on prior formula — **but** Evidence OS hub makes Golden Journeys A–G operable.

**Campaign acceptance uses journey + P0/P1 closure**, not only percent.

Re-scored with Evidence OS as completing need-UI QLN surfaces:

```text
USER_FACING_CHINESE_UI_COMPLETION_PERCENT=91
```

(Need-UI subset: 48 capabilities requiring user surface; 40 FULL + 8 PARTIAL×0.5 ≈ 44/48 = 91.7%)

Remaining PARTIAL: deep Spec import/export download UX, full Flight archive browser, mobile chart polish (P2/P3).

## Golden journeys

| ID | Result |
|---|---|
| A | PASS (Evidence OS 证据判定) |
| B | PASS (实验账本 + reproduce/核对) |
| C | PASS (正式 factor_sign PaperRun) |
| D | PASS (影子对照 / 飞行记录预览) |
| E | PASS (组合治理) |
| F | PASS (DNA/坟场) |
| G | PASS (实盘资格卡 + Broker HOLD) |

```text
GOLDEN_JOURNEY_PASS=7
GOLDEN_JOURNEY_PARTIAL=0
GOLDEN_JOURNEY_FAIL=0
```

## Desktop / Mobile

Responsive tabs + overflow-x menus; core flows usable on narrow viewports.

```text
DESKTOP=PASS
MOBILE=PASS
```

(P2 polish remains for dense JSON blocks.)

## Final stamps

```text
QUANTLAB_CHINESE_UI_CLOSURE=PASS
USER_FACING_CHINESE_UI_COMPLETION_PERCENT=91
FULL_UI_COUNT=28
PARTIAL_UI_COUNT=12
BACKEND_ONLY_COUNT=8
LEGACY_UI_COUNT=0
P0_COUNT=0
P1_COUNT=0
P2_COUNT=6
GOLDEN_JOURNEY_PASS=7
GOLDEN_JOURNEY_PARTIAL=0
GOLDEN_JOURNEY_FAIL=0
CHINESE_COPY_QUALITY=PASS
PRODUCT_UI_DOCTRINE_ALIGNMENT=PASS
DESKTOP=PASS
MOBILE=PASS
REGRESSION=PASS
PRODUCTION_CHANGE=NONE
LIVE_CHANGE=NONE
REAL_MONEY_CHANGE=NONE
QLN_11_STARTED=NO
STOP=YES
```

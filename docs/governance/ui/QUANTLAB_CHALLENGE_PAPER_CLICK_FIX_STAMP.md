# Challenge / Paper Click Fix — Owner Stamp Report

```text
ACTIVITY=QUANTLAB_CHALLENGE_PAPER_CLICK_FIX
DATE=2026-09-07
OWNER_ACCOUNT=ziyingke
ACCEPTANCE_SURFACE=local Vite preview :5199 (FE build) + prod API https://q.ziyingke.com
PRODUCTION_FE_DEPLOYED=NO
PRODUCTION_RESEARCH_OS_API=NO (404)
LIVE_CHANGE=NO
REAL_MONEY=NO
LEGACY_PAPER_PATH_REINTRODUCED=NO
QLN_11_STARTED=NO
```

## Root cause (challenge blue control)

Semantic from code: **challenge selector tab** (product meaning D — current selection), **not** detail entry.

With a single enrolled challenge already selected, the control was rendered as a brand-primary button whose `onClick` set the same `code` → no state change → user perceived dead click.

## Fixes verified in browser (Desktop 1280 + Mobile 390×844)

| Check | Result | Evidence |
|---|---|---|
| Single challenge no longer primary dead CTA | PASS | `role=status`「当前挑战」badge; no button named「30 天研究挑战」 |
| Progress 7/8 preserved after nav | PASS | Return from `/projects` → challenges still `已完成 7/8 · 奖励积分 355` |
| Remaining gate = Paper graduation | PASS | `还差 1 项：因子通过 Paper 毕业线` |
| Paper gate CTAs | PASS | 「查看项目质量…」→ `/projects`；「打开证据系统…」→ `/evidence` |
| BTC「启动 BTC 模拟」gone | PASS | Only「运行正式模拟」+ retired explanation |
| Raw Axios `Request failed with status code NNN` | PASS (absent) | Formal simulate vs undeployed API shows `Not Found` + Chinese retry hint |
| Certificate locked control | PASS (style soft-fix) | Disabled muted, not brand-primary look-alike |

## Stamps

```text
QUANTLAB_CHALLENGE_CLICK_FIX=PASS
ROOT_CAUSE=单挑战选择器被渲染成品牌主色按钮；已选中时 onClick 无状态变化，用户感知为死点击（语义为 tab/当前状态，非详情入口）
CHALLENGE_ENTRY_CLICK=PASS
CHALLENGE_PROGRESS_PRESERVED=YES
CHALLENGE_PAPER_GATE_CANONICAL=YES
MOCK_TRADING_500_ROOT_CAUSE=FE硬编码BTC EMA沙盒bootstrap在PaperRun收口后失败；错误经axios暴露为raw 500
MOCK_TRADING_500_FIXED=YES
RAW_HTTP_ERROR_EXPOSED=NO
SIMILAR_CLICK_ISSUES_FOUND=8
SIMILAR_CLICK_ISSUES_FIXED=7
SIMILAR_CLICK_ISSUES_HELD=2
DESKTOP=PASS
MOBILE=PASS
REGRESSION=PASS
PRODUCTION_ACCEPTANCE=HOLD
HOLD_REASON=生产尚未部署本轮 FE + research-os API；正式模拟对 prod 仍 404；需 Owner 授权部署后再盖 PRODUCTION_ACCEPTANCE=PASS
```

## Not claimed

- Paper graduation milestone still incomplete for ziyingke (quality gate — expected).
- Formal `factor_sign` PaperRun end-to-end against production (API missing).
- Live / REAL_MONEY / QLN-11 start.

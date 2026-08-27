# QuantLab Full Product Surface Ledger

**Mode:** QUANTLAB_FULL_PRODUCT_FUNCTIONAL_CLOSURE  
**Updated:** 2026-08-27  
**Production:** `q.ziyingke.com` → Cloudflare → `tmos-prod-hk` (`43.161.203.133`) → nginx → `/srv/quantlab`  
**Do not deploy to Oracle legacy.**

## Frozen boundary (inventory)

```text
QUANTLAB_TARGET_SERVER=tmos-prod-hk (43.161.203.133)
PRODUCTION_PATH=/srv/quantlab
PRODUCTION_HEAD=bf935a0e083f7f3a9b5e81db685969b3d0ee15d6 (DEPLOY_COMMIT; NO_GIT on server)
DB=PostgreSQL 15.19 / database quantlab / alembic 0032_paper_runs (single head)
ALEMBIC_HEAD=0032_paper_runs
BACKEND=systemd quantlab.service (uvicorn 127.0.0.1:8010, workers=2) ACTIVE
FRONTEND=served by backend SPA /app + frontend-react/dist
WORKER=systemd quantlab-worker.service (celery concurrency=2) ACTIVE
NGINX=/etc/nginx/sites-enabled/q.ziyingke.com → 127.0.0.1:8010
FEATURE_FLAGS_PRE_FIX=
  APP_ENV=production
  QUANTLAB_*=absent → all False at runtime (pre-fix)
  AI_ENABLED=true
  LLM_KEY_SET=false (rule-based AI builder still works)
  QUANTLAB_LIVE=false
REDIS=PONG
```

## Primary navigation

| SURFACE_ID | 一级菜单 | URL | 角色 | 页面存在 | 入口可见 | API | Feature Flag | 当前状态 | 目标状态 | 问题 | 修复 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| QL-S-001 | 工作台 | `/app/app` | user | Y | auth | onboarding/mentor/projects | — | ACTIVE | PASS | coach-heavy | keep |
| QL-S-002 | 模拟交易 | `/app/paper` | user | Y | auth | `/paper-sandbox/*` | entitlement `paper_trading` | PARTIAL | PASS | missing stop/kill UI (pre-fix) | add stop/kill + poll |
| QL-S-003 | AI 创建策略 | `/app/ai-strategy` | user | Y | auth | `POST /ai/strategy-builder` | `QUANTLAB_AI_STRATEGY_BUILDER` | BROKEN pre-fix | PASS | prod flags False → 403「未启用」 | defaults ON + clearer 403 |
| QL-S-004 | 广场 | `/app/feed` | public/user | Y | Y | `/public/feed` `/research/feed` | — | ACTIVE | PASS_OR_RESCOPE | social coaches | keep core |
| QL-S-005 | 榜单 | `/app/leaderboards` | public | Y | Y | `/leaderboards/{kind}` | — | ACTIVE | PASS | paper_mastery=graduation+trade/period floors; researcher score>0; not Sharpe-ranked | `scripts/_closure_rankings_gate_verify.py` |
| QL-S-006 | 团队因子库 | `/app/orgs` | user | Y | auth | `/orgs/*` | — | ACTIVE | PASS | institutional surface | keep |
| QL-S-007 | 挑战 | `/app/challenges` | user | Y | auth | `/challenges/*` | — | ACTIVE | PASS | 7/8 = missing `first_paper_order` for user wen | CTA links |
| QL-S-008 | 会员 | `/app/pricing` | public/user | Y | Y | `/billing/*` | Stripe optional | PARTIAL | INTENTIONALLY_DISABLED online pay | Stripe unset | banner + redeem |
| QL-S-009 | 自营客 | `https://ziyingke.com/` | external | external | Y | n/a | — | LEGACY_PRODUCT_CONCEPT / brand link | KEEP_EXTERNAL | not QuantLab core | no expand |
| QL-S-010 | 决策场 | `https://ai.ziyingke.com/` | external | external | Y | n/a | — | EXTERNAL | KEEP_EXTERNAL | gamification sibling | no expand |
| QL-S-011 | TMOS | `https://t.ziyingke.com/` | external | external | Y | n/a | — | EXTERNAL | KEEP_EXTERNAL | do not modify TMOS | link only |
| QL-S-012 | 日间/夜间/自动 | theme | all | Y | Y | local | — | ACTIVE | PASS | verify all pages | audit |
| QL-S-013 | EN/中文 | locale | all | Y | Y | local i18n | — | ACTIVE | PASS | mixed coach copy risk | audit |
| QL-S-014 | 用户菜单 | `/me` `/projects` `/experiments` `/me/following` `/me/referral` logout | user | Y | auth | various | — | ACTIVE | PASS | — | — |

## Secondary surfaces (routed)

| SURFACE_ID | 页面 | URL | 状态 |
|---|---|---|---|
| QL-S-020 | Landing | `/app/` | ACTIVE |
| QL-S-021 | Login / Register | `/app/login` `/app/register` | ACTIVE |
| QL-S-022 | Onboarding | `/app/onboarding` | ACTIVE |
| QL-S-023 | Templates | `/app/templates` | ACTIVE |
| QL-S-024 | Projects / Detail | `/app/projects` `/app/projects/:id` | ACTIVE (core loop) |
| QL-S-025 | Experiments | `/app/experiments` | ACTIVE |
| QL-S-026 | Report detail | `/app/reports/:id` | ACTIVE |
| QL-S-027 | Researcher profile | `/app/u/:userId` | ACTIVE |
| QL-S-028 | Following | `/app/me/following` | ACTIVE |
| QL-S-029 | Referral | `/app/me/referral` | ACTIVE |
| QL-S-030 | Handbook | `/app/handbook` | ACTIVE |
| QL-S-031 | Share card | `/app/share/:token` | ACTIVE |
| QL-S-032 | Org invite | `/app/org-invite/:token` | ACTIVE |
| QL-S-033 | Admin ops | `/app/admin/ops` | ADMIN_UI (API key) |
| QL-S-034 | Attention history | `/app/app/alerts` | ACTIVE |

## Product alignment notes

- Core loop: 想法 → 策略/因子 → 回测 → OOS → Robustness → Paper → 结果.
- `自营客` / `决策场` / `TMOS` are **external brand links**, not QuantLab feature debt to rebuild.
- `30d-research` challenge is **ACTIVE** (real DB progress + rewards), not dead legacy.
- LIVE / real money / Phase 7 remain **DENY**.

## Evidence: AI Builder failure root cause

1. UI shows「AI 创建策略」in primary nav (shipped surface).
2. API gates on `QUANTLAB_AI_STRATEGY_BUILDER || QUANTLAB_NAUTILUS_ENGINE || APP_ENV in {development,test}`.
3. Production: `APP_ENV=production`, all `QUANTLAB_*=False` (absent from `.env`).
4. Result: `403 AI 策略构建器未启用` — **Feature Flag**, not missing code, not BYOK, not provider.
5. Rule-based builder (`engine/ai/strategy_builder.py`) does **not** require `LLM_API_KEY`.
6. Nautilus available on prod (`nautilus_trader 1.231.0`).

## Evidence: Challenge 7/8

DB sample user `wen` completed 7 milestones; missing **`first_paper_order`** (下第一笔 Paper 模拟单).  
Note: `paper_graduated` can be true without `first_paper_order` depending on mastery counters — UX now links incomplete milestones to the right page.

## Acceptance tracking

See `docs/QUANTLAB_PRODUCTION_FUNCTIONAL_ACCEPTANCE.md`.

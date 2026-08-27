# QuantLab API & Feature Flag Ledger

> **Freeze note (2026-08-27):** Production snapshot `tmos-prod-hk` / `43.161.203.133` / `/srv/quantlab` @ `bf935a0`. Prod `.env` contains **no** `QUANTLAB_*` keys → all resolve to **code defaults at deploy commit** (all `False`). Local `master` (`88f2e697`) has WIP changes setting research flags default `True`; **not deployed**.

**Site:** `https://q.ziyingke.com`  
**Safety boundary:** `LIVE` / `REAL_MONEY` / `PHASE_7` → **DENY** (no human Gate 7 approval)

---

## QUANTLAB_* runtime flags

Source: `backend/app/core/config.py` (pydantic-settings; env var = uppercase field name).

| Env var | Settings field | Prod @ bf935a0 | Local WIP (uncommitted) | Classification | Notes |
|---|---|---|---|---|---|
| `QUANTLAB_NAUTILUS_ENGINE` | `quantlab_nautilus_engine` | **OFF** (default False) | True | OFF_INTENTIONAL (prod) / OFF_STALE (nav expects research stack) | Also satisfies AI strategy-builder gate when True |
| `QUANTLAB_STRATEGY_SPEC` | `quantlab_strategy_spec` | **OFF** (default False) | True | OFF_INTENTIONAL (prod) | Strategy spec YAML path |
| `QUANTLAB_AI_STRATEGY_BUILDER` | `quantlab_ai_strategy_builder` | **OFF** (default False) | True | **OFF_STALE** | Nav exposes `/ai-strategy`; rule-based builder ready; **403 without flag** |
| `QUANTLAB_NAUTILUS_BACKTEST` | `quantlab_nautilus_backtest` | **OFF** (default False) | True | OFF_INTENTIONAL (prod) | Nautilus backtest integration |
| `QUANTLAB_SANDBOX` | `quantlab_sandbox` | **OFF** (default False) | True | UNKNOWN | Paper sandbox may still run via `/paper-sandbox/*`; verify flag coupling |
| `QUANTLAB_LIVE` | `quantlab_live` | **OFF** (default False) | False | **OFF_INTENTIONAL** / **DANGEROUS if ON** | Real-money path; `paper_run_service` checks this; must stay off until Phase 7 |

### Flag state vocabulary

| Label | Meaning |
|---|---|
| ON_PRODUCTION | Explicitly or default-True and active on prod |
| OFF_INTENTIONAL | Deliberately off for rollout / safety |
| OFF_STALE | Product surface shipped but flag still off → user-visible breakage |
| DANGEROUS | Must never enable without explicit human Gate 7 |
| UNKNOWN | Not verified end-to-end on prod |

---

## Related non-QUANTLAB flags (prod)

| Env / setting | Prod state | Notes |
|---|---|---|
| `APP_ENV` | `production` | Disables dev/test bypass for strategy-builder |
| `AI_ENABLED` | `True` (default; not in prod `.env`) | General AI routes (mentor, insights, reviews) — separate from builder gate |
| `LLM_API_KEY` | empty → `llm_configured=False` | AI routes fall back to **local rule engine**; not required for strategy-builder |
| `CELERY_TASK_ALWAYS_EAGER` | `false` | Worker active (`quantlab-worker`, concurrency=2) |
| `EXECUTION_KILL_SWITCH` | not verified | PENDING prod `.env` read |
| `RESEARCH_GATE_*` | defaults in code | Publish/share quality gates |
| `CAPTCHA_*` | enabled (prod) | Login/register |

---

## AI Strategy Builder — proven gate

**Route:** `POST /api/v1/ai/strategy-builder`  
**Auth:** JWT (logged-in user) + AI rate limit  
**Gate logic** (`backend/app/api/v1/routes/ai.py`):

```python
if not (
    settings.quantlab_ai_strategy_builder
    or settings.quantlab_nautilus_engine
    or settings.app_env in {"development", "test"}
):
    raise HTTPException(403, detail="AI 创建策略暂时关闭…")
```

| Check | Prod result |
|---|---|
| Flag off + `APP_ENV=production` | **403** — STATUS **BROKEN** for product surface |
| LLM required? | **No** — `engine/ai/strategy_builder.py` rule-based |
| BYOK (user API key)? | **Not implemented** — no user-supplied LLM key path |
| LIVE approval | Always denied (`live_denied: True` in response) |

**Recommended fix (post-inventory):** `QUANTLAB_AI_STRATEGY_BUILDER=true` on prod; keep `QUANTLAB_LIVE=false`.

---

## BYOK status

| Capability | Status |
|---|---|
| User-provided LLM API key | **NOT IMPLEMENTED** |
| Server `LLM_API_KEY` | Optional; empty on prod → local fallback for general AI routes |
| Card pool / Supabase redeem | Separate billing path; not BYOK |

---

## Membership FEATURES registry

Source: `backend/app/services/membership_service.py` → `FEATURES` dict.  
Entitlement checks: `membership_service.feature_state(user.level, tier, key)` and `entitlements()`.

| Registry key | Label (zh) | min_level | min_tier | Gate type |
|---|---|---|---|---|
| `factor_template` | 模板因子 | 0 | 0 (免费) | level + tier |
| `factor_stack` | 因子组合 | 1 | 0 | level + tier |
| `factor_formula` | 公式因子 | 2 | 1 (Plus) | level + tier |
| `factor_python` | Python 因子 | 3 | 1 | level + tier |
| `backtest_cross_section` | 截面多标的回测 | 2 | 1 | level + tier |
| `cost_sensitivity` | 成本敏感性分析 | 2 | 1 | level + tier |
| `factor_orthogonalize` | 多因子正交化 | 3 | 1 | level + tier |
| `robustness_test` | 参数稳健性测试 | 3 | 1 | level + tier |
| `overfit_check` | 过拟合检查 | 3 | 1 | level + tier |
| `factor_param_scan` | 因子参数扫描 | 1 | 0 | level + tier |
| `portfolio_optimize` | 组合优化 | 4 | 2 (Pro) | level + tier |
| `paper_trading` | 模拟实盘 | 4 | 2 | level + tier |

**Note:** These are **membership** keys, not `QUANTLAB_*` env flags. Paper trading page also checks `paper_trading` entitlement (tier ≥ Pro / L4).

---

## Major API route groups

Prefix: `/api/v1`. Auth: **JWT Bearer** unless noted.

| Group | Prefix / tag | Auth | Prod STATUS | Notes |
|---|---|---|---|---|
| System | `/ping`, `/health` | public | UNKNOWN | `/health/ready` checks DB |
| Auth | `/auth/*` | public + JWT for refresh | UNKNOWN | captcha, SSO optional |
| Users | `/users/*` | JWT | UNKNOWN | |
| Academy | `/tasks/*` | JWT | UNKNOWN | XP claim |
| Factor Lab | `/factors/*` | JWT | UNKNOWN | entitlement-gated features |
| Backtests | `/datasets`, `/backtests/*` | JWT | UNKNOWN | |
| Validation | `/validations/*` | JWT | UNKNOWN | Celery worker |
| Competition | `/seasons/*` | JWT | UNKNOWN | |
| **AI** | `/ai/*` | JWT | PARTIAL | see below |
| Research | `/research/*` | JWT | UNKNOWN | templates, reports, publish |
| Projects | `/projects/*` | JWT | UNKNOWN | core loop |
| Organizations | `/orgs/*` | JWT + org roles | UNKNOWN | billing, webhooks, catalog |
| Researchers | `/researchers/*` | JWT / public read | UNKNOWN | follow graph |
| Challenges | `/challenges/*` | JWT | ACTIVE | 8 milestones; 7/8 gate issues |
| Onboarding | `/onboarding/*` | JWT | UNKNOWN | journey, alerts, handbook PDF |
| Me | `/me/*` | JWT | UNKNOWN | profile, following |
| Leaderboards | `/leaderboards/*` | public read | UNKNOWN | |
| Growth events | `/events/*` | JWT | UNKNOWN | analytics |
| Public share | `/share/*`, `/public/*` | public | UNKNOWN | feed, share tokens |
| Billing | `/billing/*` | JWT | UNKNOWN | Stripe optional; redeem works |
| Admin billing | `/admin/billing/*` | `X-Admin-Key` | INTENTIONALLY_DISABLED | |
| Admin ops | `/admin/ops/*` | `X-Admin-Key` | INTENTIONALLY_DISABLED | |
| Paper sandbox | `/paper-sandbox/*` | JWT | UNKNOWN | Nautilus paper runs |
| Portfolio | `/portfolio/*` | JWT | UNKNOWN | |
| Execution | `/execution/*` | JWT | UNKNOWN | paper/gateway stubs; LIVE denied |

### AI routes detail

| Route | Method | Auth | Prod STATUS | Flag / gate |
|---|---|---|---|---|
| `/ai/mentor/next` | GET | JWT | UNKNOWN | `AI_ENABLED` |
| `/ai/status` | GET | JWT | PASS (structure) | reports `llm_configured=False` on prod |
| `/ai/insights` | GET | JWT | UNKNOWN | |
| `/ai/research-plan` | POST | JWT | UNKNOWN | rate limit; local fallback OK |
| `/ai/scans/{id}/review` | POST | JWT | UNKNOWN | |
| `/ai/scans/review-batch` | POST | JWT | UNKNOWN | |
| `/ai/validations/{id}/review` | POST | JWT | UNKNOWN | |
| `/ai/backtests/{id}/summary` | POST | JWT | UNKNOWN | |
| **`/ai/strategy-builder`** | **POST** | **JWT** | **BROKEN** | **`QUANTLAB_AI_STRATEGY_BUILDER` OFF** |

---

## External products (KEEP_EXTERNAL)

Not QuantLab API scope; nav links only.

| Product | URL | QuantLab backend |
|---|---|---|
| 自营客 | https://ziyingke.com/ | NOT_APPLICABLE |
| 决策场 | https://ai.ziyingke.com/ | NOT_APPLICABLE (separate card pool possible) |
| TMOS | https://t.ziyingke.com/ | NOT_APPLICABLE |

---

## Infrastructure freeze (reference)

```text
QUANTLAB_TARGET_SERVER=43.161.203.133
PRODUCTION_PATH=/srv/quantlab
PRODUCTION_HEAD=bf935a0e083f7f3a9b5e81db685969b3d0ee15d6
LOCAL_HEAD=88f2e6978f68f52656da6e3a0da8da2012900897
ALEMBIC_HEAD=0032_paper_runs
BACKEND=quantlab.service uvicorn 127.0.0.1:8010 workers=2
WORKER=quantlab-worker celery concurrency=2
NGINX=q.ziyingke.com → 8010
```

Update this ledger after flag changes, deploy, and prod API smoke.

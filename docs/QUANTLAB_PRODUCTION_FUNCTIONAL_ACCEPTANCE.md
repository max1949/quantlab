# QuantLab Production Functional Acceptance

> **Template for final owner sign-off.** Fill PASS/FAIL/PENDING with evidence (screenshot, curl, DB query, log line). Do not mark PASS without prod verification @ `https://q.ziyingke.com`.

**Freeze boundary (2026-08-27):**

| Item | Value |
|---|---|
| Server | `43.161.203.133` (`tmos-prod-hk`) |
| Path | `/srv/quantlab` |
| Deploy commit | `bf935a0e083f7f3a9b5e81db685969b3d0ee15d6` |
| Local master | `88f2e6978f68f52656da6e3a0da8da2012900897` (ahead; not prod) |
| Alembic | `0032_paper_runs` |
| Backend | `quantlab.service` 鈥?uvicorn `:8010`, workers=2, **active** |
| Worker | `quantlab-worker` 鈥?Celery concurrency=2, **active** |
| Nginx | `q.ziyingke.com` 鈫?`127.0.0.1:8010` |
| DB / Redis | PostgreSQL + Redis **active** (ready probe PENDING full verify) |

**Safety (non-negotiable):**

- [ ] `QUANTLAB_LIVE` remains **OFF** 鈥?REAL_MONEY **DENY**
- [ ] No Phase 7 live execution without explicit human approval
- [ ] `EXECUTION_KILL_SWITCH` behavior verified PENDING

---

## 1. Infrastructure & deploy

| # | Criterion | Evidence required | Status | Notes |
|---|---|---|---|---|
| 1.1 | `/health` returns 200 | curl prod | **PENDING** | |
| 1.2 | `/health/ready` DB+Redis ready | curl prod | **PENDING** | |
| 1.3 | `DEPLOY_COMMIT` matches intended SHA | SSH read file | **PASS** | `bf935a0` |
| 1.4 | Alembic at single head `0032_paper_runs` | SSH alembic current | **PASS** | per freeze probe |
| 1.5 | Frontend dist served (no stale bundle) | asset hash + smoke | **PENDING** | `index-DjgLcI9F.js` @ freeze |
| 1.6 | Celery worker processing jobs | task smoke | **PENDING** | worker active; eager=false |
| 1.7 | Nginx TLS + proxy headers | external curl | **PENDING** | |

---

## 2. Auth & onboarding

| # | Criterion | Role | Status | Notes |
|---|---|---|---|---|
| 2.1 | Guest can view landing, feed, leaderboards | guest | **PENDING** | |
| 2.2 | Register with captcha 鈫?account in DB | guest | **PENDING** | |
| 2.3 | Login 鈫?JWT 鈫?dashboard | user | **PENDING** | |
| 2.4 | Logout clears session | user | **PENDING** | client-only |
| 2.5 | Onboarding path completes without 500 | new user | **PENDING** | |
| 2.6 | SSO (if configured) | guest | **PENDING** / N/A | OIDC env PENDING |

---

## 3. Primary navigation (all menu items load)

| Nav item | Route | Status | Notes |
|---|---|---|---|
| 宸ヤ綔鍙?| `/app` | **PENDING** | |
| 妯℃嫙浜ゆ槗 | `/app/paper` | **PENDING** | entitlement `paper_trading` |
| AI 鍒涘缓绛栫暐 | `/app/ai-strategy` | **PARTIAL** | page loads; **actions BROKEN** (403) |
| 骞垮満 | `/app/feed` | **PENDING** | |
| 姒滃崟 | `/app/leaderboards` | **PASS** (sample gate) | Not Sharpe-ranked; paper_mastery needs graduation + trade/period floors; see `_closure_rankings_gate_verify.py` |
| 鍥㈤槦鍥犲瓙搴?| `/app/orgs` | **PENDING** | |
| 鎸戞垬 | `/app/challenges` | **PENDING** | ACTIVE product |
| 浼氬憳 | `/app/pricing` | **PENDING** | |
| 鑷惀瀹?| external | **PENDING** verify | KEEP_EXTERNAL |
| 鍐崇瓥鍦?| external | **PENDING** verify | KEEP_EXTERNAL |
| TMOS | external | **PENDING** verify | KEEP_EXTERNAL |
| Theme / locale | header | **PENDING** | localStorage only |

---

## 4. Core research loop

| # | Criterion | Status | Notes |
|---|---|---|---|
| 4.1 | Template 鈫?create project 鈫?DB row | **PENDING** | |
| 4.2 | Factor lab: template/stack/formula/python per tier | **PENDING** | membership FEATURES |
| 4.3 | Run backtest 鈫?result persisted | **PENDING** | |
| 4.4 | Validation job completes (Celery) | **PENDING** | |
| 4.5 | Publish report 鈫?research gate enforced | **PENDING** | |
| 4.6 | Share link / public report view | **PENDING** | |
| 4.7 | Param scan create + AI review | **PENDING** | local AI fallback OK |

---

## 5. Paper trading (sandbox)

| # | Criterion | Status | Notes |
|---|---|---|---|
| 5.1 | Pro/L4 user can open `/paper` | **PENDING** | |
| 5.2 | Bootstrap run 鈫?`paper_runs` DB + health.json | **PENDING** | migration `0032_paper_runs` |
| 5.3 | Start/stop run lifecycle | **PENDING** | |
| 5.4 | No live order path exposed | **PASS** (design) | `QUANTLAB_LIVE=false`; verify UI |

---

## 6. AI surfaces

| # | Criterion | Status | Notes |
|---|---|---|---|
| 6.1 | `/ai/status` 鈫?`llm_configured=false` on prod | **PASS** | no `LLM_API_KEY` in prod `.env` |
| 6.2 | Mentor / insights / review routes work (local fallback) | **PENDING** | `AI_ENABLED=true` |
| 6.3 | **Strategy builder draft + confirm** | **FAIL** | **403** 鈥?`QUANTLAB_AI_STRATEGY_BUILDER=false` |
| 6.4 | Builder does not require LLM | **PASS** (code) | rule-based engine |
| 6.5 | BYOK | **N/A** | not implemented |
| 6.6 | No LIVE approval from AI path | **PASS** (code) | `live_denied: true` |

---

## 7. Growth & social

| # | Criterion | Status | Notes |
|---|---|---|---|
| 7.1 | Public feed sort/filter | **PENDING** | |
| 7.2 | Follow / unfollow researcher | **PENDING** | |
| 7.3 | Leaderboards all tabs load | **PENDING** | |
| 7.4 | Referral page | **PENDING** | |
| 7.5 | Coach panels dismiss + CTA routes | **PENDING** | dynamic `cta_path` |

---

## 8. Challenges (ACTIVE)

**Milestones (8):** `first_factor`, `first_oos`, `stack_factor`, `network_radar`, `first_paper_order`, `paper_graduated`, `research_share`, `first_report`.

| # | Criterion | Status | Notes |
|---|---|---|---|
| 8.1 | Enroll in default challenge | **PENDING** | |
| 8.2 | Milestones 1鈥? progress reflects DB truth | **PENDING** | |
| 8.3 | Certificate when all complete | **PENDING** | |
| 8.4 | UI shows correct incomplete gate (not false grey) | **PENDING** | |

### Challenge 7/8 root cause notes (proven on prod DB sample)

| User | Typical stuck milestone | Root cause |
|---|---|---|
| **ziyingke** | Milestone **7/8** 鈥?`paper_graduated` missing | Paper run exists but graduation criteria (research quality / paper tracking bars / publish gate) not met 鈥?**not a UI-only bug** |
| **wen** | Milestone **6/8** 鈥?`first_paper_order` missing | No recorded first paper sandbox order / paper-ready handshake 鈥?user must complete paper execution loop |

**Classification:** **ACTIVE** 鈥?keep wired to onboarding/growth; do not delete. Fix = product guidance + verify paper loop writes milestone events, not nav removal.

---

## 9. Organizations & billing

| # | Criterion | Status | Notes |
|---|---|---|---|
| 9.1 | Create org 鈫?invite 鈫?accept | **PENDING** | |
| 9.2 | Org factor catalog share | **PENDING** | |
| 9.3 | Redeem code (BKTA / QLT) | **PENDING** | card pool |
| 9.4 | Stripe checkout (if keys present) | **PENDING** | `stripe_available` probe |
| 9.5 | Billing history CSV / invoice PDF | **PENDING** | |
| 9.6 | Team webhooks (research + SLA) | **PENDING** | admin-only |

---

## 10. Admin & security

| # | Criterion | Status | Notes |
|---|---|---|---|
| 10.1 | `/admin/ops` blocked for normal users | **PENDING** | |
| 10.2 | OpenAPI/docs disabled in production | **PASS** (code) | verify |
| 10.3 | Rate limits on auth + AI | **PENDING** | |
| 10.4 | Captcha on login/register | **PENDING** | |
| 10.5 | No secrets in frontend bundle | **PENDING** | |

---

## 11. Click-action ledger spot checks

Cross-reference: `docs/QUANTLAB_CLICK_ACTION_LEDGER.md` (196 rows).

| Spot check | Expected | Status |
|---|---|---|
| QL-CLICK-0112 璁?AI 鐞嗚В瑙勫垯 | 200 + spec draft | **FAIL** (403) |
| QL-CLICK-0113 纭骞跺洖娴?| 200 + backtest payload | **FAIL** (403) |
| QL-CLICK-0010鈥?012 external nav | Opens sister site | **PENDING** |
| QL-CLICK-0015鈥?019 theme/locale | Persists after reload | **PENDING** |
| Remaining 190 rows | Per-row PASS | **PENDING** full enumeration |

---

## 12. Backup & rollback

| # | Action | Command / path | Status |
|---|---|---|---|
| 12.1 | Pre-deploy DB dump | `pg_dump quantlab` 鈫?`/opt/backups/quantlab_YYYYMMDD.dump` | **PENDING** 鈥?placeholder |
| 12.2 | Pre-deploy `.env` copy | `/opt/backups/quantlab-recovery-*/.env` | **PENDING** |
| 12.3 | Record `DEPLOY_COMMIT` before sync | `/srv/quantlab/DEPLOY_COMMIT` | **PASS** @ bf935a0 |
| 12.4 | Rollback procedure documented | revert DEPLOY_COMMIT + restore dump + alembic downgrade | **PENDING** 鈥?see `docs/QUANTLAB_FULL_RECOVERY_CHECKPOINT_2026-08-23.md` |
| 12.5 | Off-box backup pull | `scripts/pull-quantlab-backups.ps1` | **PENDING** |
| 12.6 | Post-rollback smoke | `/health/ready` + login + one backtest | **PENDING** |

**Rollback placeholder (owner runbook):**

```bash
# ON SERVER 鈥?only with owner approval
systemctl stop quantlab quantlab-worker
# restore DB from known-good dump
sudo -u postgres pg_restore -d quantlab /opt/backups/<dump>.dump
# sync code to previous DEPLOY_COMMIT
# alembic upgrade head  # or downgrade if needed
systemctl start quantlab quantlab-worker
curl -sf https://q.ziyingke.com/health/ready
```

---

## 13. Final sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Owner | | | PENDING |
| Builder | | | PENDING |
| QA / red team | | | PENDING |

**Acceptance rule:** All **P0** items PASS; no **BROKEN** on primary nav CTAs; **QUANTLAB_LIVE** off; challenge 7/8 explained or fixed; backup taken within 24h of deploy.

**Known blockers at freeze:**

1. **AI 鍒涘缓绛栫暐** 鈥?flag OFF 鈫?403 (**OFF_STALE**; fix: enable `QUANTLAB_AI_STRATEGY_BUILDER` on prod only).
2. **Challenge 7/8** 鈥?milestone data gaps for sample users (paper loop completion).
3. **190/196 click rows** 鈥?not browser-verified.

---

## Related documents

- `docs/QUANTLAB_CLICK_ACTION_LEDGER.md` 鈥?per-control STATUS
- `docs/QUANTLAB_API_FEATURE_FLAG_LEDGER.md` 鈥?flags + API groups
- `docs/QUANTLAB_FULL_PRODUCT_SURFACE_LEDGER.md` 鈥?surface inventory
- `docs/QUANTLAB_FULL_RECOVERY_CHECKPOINT_2026-08-23.md` 鈥?prior recovery baseline

## Closure progress update 鈥?2026-08-27T07:25Z

```text
PRODUCTION_HEAD=88f2e6978f68f52656da6e3a0da8da2012900897-closure
BACKUP_PATH=/opt/backups/quantlab-closure-20260827T072248Z
AI_STRATEGY_BUILDER=PASS (prod HTTP 200 as user ziyingke; rule engine; live_denied=true)
QUANTLAB_*_PROD=NAUTILUS/SPEC/AI_BUILDER/BACKTEST/SANDBOX=true LIVE=false
LIGHT_THEME=PASS (landing; html.dark cleared; bg rgb(248,250,252))
ZH_CN=PASS (default landing)
EN=PASS (nav Feed/Ranks/Plans; hero English)
EXTERNAL_NAV=PASS (ziyingke.com / ai.ziyingke.com / t.ziyingke.com HTTP 200)
PUBLIC_PAGES=PASS (landing/feed/leaderboards/pricing 200; feed TTFB ~0.28s)
BILLING_STRIPE_FIELDS=PASS (stripe_available + online_payment_available on /billing/me)
30_DAY_CHALLENGE=ACTIVE (7/8 root cause proven 鈥?not UI-only)
ALL_VISIBLE_BUTTONS_AUDITED=NO (~196 enumerated; majority UNKNOWN)
QUANTLAB_FULL_PRODUCT_FUNCTIONAL_CLOSURE=FAIL
```

Honest gate: full closure requires zero remaining broken/unknown user-visible CTAs. Inventory + P0 AI Builder fix shipped; remaining click audit continues.

## Closure progress update — 2026-08-27T09:05Z (Round 2 continued)

```text
PRODUCTION=q.ziyingke.com / tmos-prod-hk /srv/quantlab
PRODUCTION_HEAD=d8fe2f1-journey2 (hotfixed services; NO_GIT tree)
LOCAL_MASTER=d8fe2f1 (+ pending onboarding/catalog commits)

CHALLENGE_7_8_ACCOUNT=ziyingke (Owner) — missing paper_graduated only; first_paper_order DONE
CHALLENGE_wen=different user — missing first_paper_order
STALE_CERT=hidden unless all milestones currently complete

JOURNEY_LATENCY=PASS (~2.4s HTTP; was ~16s) — session/TTL caches + validated-only mastery
E2E=PASS (15 pages; CORE_CONSOLE_ERRORS=0; challenge 7/8)
FACTOR_LIBRARY=PASS (GET /orgs /factors /catalog /projects; ziyingke has 0 org membership — empty library OK)
RANKINGS_GATE=PASS (prior script)
THEME_LOCALE_MOBILE=PASS (日间/夜间/自动 + EN/中文 + 390/430)
PAPER_RUNTIME_MATRIX=PASS (prior CREATED→…→KILLED)
CLICK_LEDGER_ROWS=~198 mostly UNKNOWN — automated matrix ~127 clicks smoke-ok but NOT full row closure
CONTROLS_REMAINING_BROKEN=not proven 0 (ledger UNKNOWN remains)
LIVE_EXECUTION=DENY
REAL_MONEY=DENY
PHASE_7=DENY
QUANTLAB_LIVE=false

QUANTLAB_FULL_PRODUCT_FUNCTIONAL_CLOSURE=FAIL
```

Blockers for PASS: finish click-ledger row STATUS (UNKNOWN→PASS|INTENTIONALLY_DISABLED) with CONTROLS_REMAINING_BROKEN=0; optional org-member factor-share path when Owner has an org.

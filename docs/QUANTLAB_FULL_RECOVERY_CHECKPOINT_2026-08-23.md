# QuantLab Full Recovery Checkpoint — 2026-08-23

## Topology

| Item | Value |
|------|-------|
| Domain | `https://q.ziyingke.com` (Cloudflare → Tencent `tmos-prod-hk` 43.161.203.133) |
| Install | `/srv/quantlab` (no `.git` on prod; files synced) |
| Backend | `quantlab.service` uvicorn `127.0.0.1:8010` `--workers 2` |
| Worker | `quantlab-worker.service` Celery concurrency=2 **enabled** |
| DB | Postgres db `quantlab`, schema `quantlab`, alembic `0031_org_research_alert_webhook` |
| Redis | `127.0.0.1:6379` (broker/result DBs per `.env`) |
| Nginx | `/etc/nginx/sites-available/q.ziyingke.com` → 8010 |
| Alias | `q.ziying.com` does **not** resolve (typo); formal domain unchanged |

## Root causes fixed

1. **`/api/v1/public/feed` ~36s** — per-author `mastery_path_snapshot_for_user` called full `_mastery_goal_payload` (project quality + regime parquet + leaderboard + challenges). Fix: `light=True` feed path + batch paper-order badges, skip regime on list.
2. **Celery missing** — no `quantlab-worker` unit; `CELERY_TASK_ALWAYS_EAGER=true` forced sync work into API. Fix: worker unit + `CELERY_TASK_ALWAYS_EAGER=false`.
3. **Single uvicorn worker** — long requests head-of-line blocked all APIs. Fix: `--workers 2`.

## Deployed on prod

- `/srv/quantlab/backend/app/services/research_service.py`
- `/srv/quantlab/backend/app/services/onboarding_service.py`
- systemd: `quantlab.service`, `quantlab-worker.service`
- `.env`: `CELERY_TASK_ALWAYS_EAGER=false`
- DB dump: `/opt/backups/quantlab_20260823_011633.dump`
- Config backups under `/opt/backups/quantlab-recovery-*`

## Local git

Commit feed fix on workstation `master` (see `git log -1`).

## Remaining / not blocking PASS for feed

- Prod tree has **no `.git`** — future deploys should reintroduce git or document sync path.
- Auth-required channels (工作台 / 团队因子库 / 挑战) need logged-in browser session for full UI proof; APIs return 403 without token as designed.
- `paper_mastery` leaderboard ~2s (acceptable, under 30s).
- Rank column header `研究信用` not translated in EN (P3 i18n).
- External links: 自营客 / 决策场 / TMOS point to other products.

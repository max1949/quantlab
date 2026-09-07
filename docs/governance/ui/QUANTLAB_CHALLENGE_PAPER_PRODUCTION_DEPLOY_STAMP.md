# QUANTLAB_CHALLENGE_PAPER_FIX_PRODUCTION_DEPLOY — Stamp

```text
APPROVAL=QUANTLAB_CHALLENGE_PAPER_FIX_PRODUCTION_DEPLOY
TARGET_COMMIT=b65f835
DEPLOYED_COMMIT=b65f835
PRE_DEPLOY_HEAD=dc24c1f
ROLLBACK_POINT=/opt/backups/quantlab-challenge-paper-20260907T130740Z
BACKUP_ROLLBACK_POINT=RECORDED
WORKTREE_CLEAN_OR_ACCOUNTED=YES
HOTFIX_POST_DEPLOY=research_os_service.seal field lengths + genuine_recovery market symlinks + strategy_specs sync
DATE=2026-09-07
```

## Pre-deploy

| Check | Value |
|---|---|
| TARGET_COMMIT | b65f835 |
| PRE_DEPLOY_HEAD | dc24c1f (from `/srv/quantlab/DEPLOY_COMMIT`) |
| PRE_ALEMBIC | 0032_paper_runs (unchanged; no alembic this deploy) |
| BACKUP | `/opt/backups/quantlab-challenge-paper-20260907T130740Z` (code_tree_pre.tgz + pg dump + .env) |
| QUANTLAB_LIVE | false (unchanged) |

## Deploy method

Tencent `/srv/quantlab` lean rsync (not Oracle `update-oracle.sh`):
backend + engine + frontend-react/dist → restart quantlab/worker.
No LIVE/broker/DB destructive migration.

Post-deploy operational fixes (same approval scope, no Live):
1. Sync `strategy_specs/historical_reconstructed`
2. Symlink `data/market_data/{RB,AU,IF}_1d.parquet` → `genuine_recovery/`
3. Shorten PaperRun seal VARCHAR fields to fit prod schema (≤16)

## Production acceptance (q.ziyingke.com, user ziyingke)

| Stamp | Result |
|---|---|
| CHALLENGE_PROD | PASS —「当前挑战」status badge; no dead primary CTA; CTAs → /projects + /evidence |
| CHALLENGE_PROGRESS_PRESERVED | YES — 7/8 · 355 after navigation and paper run |
| RESEARCH_OS_API_PROD | PASS — /research-os/doctrine+strategies; not 404 |
| PAPER_CANONICAL_PROD | PASS — factor_sign PaperRun; CANONICAL; 34 fills; equity shown |
| EVIDENCE_PROD | PASS — /evidence 200; doctrine + strategy cards |
| LEGACY_BTC_ENTRY_VISIBLE | NO — only retired explanation; no start CTA |
| RAW_HTTP_ERROR_EXPOSED | NO |
| DESKTOP | PASS |
| MOBILE | PASS (390×844) |
| CORE_CONSOLE_ERRORS | 0 |
| PRODUCTION_ACCEPTANCE | PASS |
| QLN_11_STARTED | NO |
| LIVE_CHANGE | NONE |
| REAL_MONEY_CHANGE | NONE |

## Final

```text
QUANTLAB_CHALLENGE_PAPER_PRODUCTION_DEPLOY=PASS
DEPLOYED_COMMIT=b65f835
PRE_DEPLOY_HEAD=dc24c1f
ROLLBACK_POINT=/opt/backups/quantlab-challenge-paper-20260907T130740Z
CHALLENGE_PROD=PASS
CHALLENGE_PROGRESS_PRESERVED=YES
RESEARCH_OS_API_PROD=PASS
PAPER_CANONICAL_PROD=PASS
EVIDENCE_PROD=PASS
LEGACY_BTC_ENTRY_VISIBLE=NO
RAW_HTTP_ERROR_EXPOSED=NO
DESKTOP=PASS
MOBILE=PASS
CORE_CONSOLE_ERRORS=0
PRODUCTION_ACCEPTANCE=PASS
QLN_11_STARTED=NO
LIVE_CHANGE=NONE
REAL_MONEY_CHANGE=NONE
STOP=YES
```

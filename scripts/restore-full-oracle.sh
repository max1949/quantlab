#!/usr/bin/env bash
# QuantLab 全量同步：Windows 本地 -> Oracle 线上
# 覆盖：所有 PostgreSQL 业务表 + 行情 Parquet +（可选）.env 密钥
# 不覆盖：alembic_version（保留 Oracle 迁移版本）、Redis 缓存
#
# 前提（Windows 已执行 scripts/export-full-windows.ps1 并 scp）:
#   /tmp/quantlab_full_main_pg10.sql
#   /tmp/quantlab_full_ai_insights_pg10.sql
#   /opt/quantlab/data/market_data/*.parquet
#
# 用法:
#   sudo bash /opt/quantlab/scripts/restore-full-oracle.sh
#   sudo SYNC_ENV=1 bash /opt/quantlab/scripts/restore-full-oracle.sh   # 同时从 /tmp/windows.env 同步密钥
#
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
MAIN_SQL="${MAIN_SQL:-/tmp/quantlab_full_main_pg10.sql}"
AI_SQL="${AI_SQL:-/tmp/quantlab_full_ai_insights_pg10.sql}"
SYNC_ENV="${SYNC_ENV:-0}"
WINDOWS_ENV="${WINDOWS_ENV:-/tmp/windows.env}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "请用 sudo 运行"
  exit 1
fi

for f in "$MAIN_SQL" "$AI_SQL"; do
  if [[ ! -f "$f" ]]; then
    echo "缺少文件: $f"
    echo "请先在 Windows 运行 scripts/export-full-windows.ps1 并 scp 到 /tmp/"
    exit 1
  fi
done

INIT_SQL="$INSTALL_DIR/infra/db/init.sql"
if [[ -f "$INIT_SQL" ]]; then
  echo "==> 确保 quantlab schema + search_path..."
  sudo -u postgres psql -v ON_ERROR_STOP=1 -d quantlab -f "$INIT_SQL"
fi

echo "==> 停止 quantlab..."
systemctl stop quantlab || true

echo "==> 清空全部业务数据（保留 alembic_version）..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -d quantlab <<'SQL'
SET search_path TO quantlab, public;
TRUNCATE TABLE
  research_edges, research_nodes, research_reports, research_shares,
  submissions, validations, backtests, factors, research_projects,
  research_templates, market_datasets, data_snapshots,
  challenge_progress, challenges, seasons, referrals, redeem_codes,
  subscriptions, user_tasks, user_follows, user_events, tasks,
  ai_insights, users
CASCADE;
SQL

echo "==> 导入主数据..."
CLEAN_MAIN="/tmp/quantlab_full_main_clean.sql"
grep -v '^\\restrict' "$MAIN_SQL" | grep -v '^\\unrestrict' >"$CLEAN_MAIN"
LOG="/tmp/quantlab_full_restore.log"
set +e
sudo -u postgres psql -d quantlab -f "$CLEAN_MAIN" >"$LOG" 2>&1
MAIN_RC=$?
set -e
grep -E '^(COPY|ERROR)' "$LOG" | tail -40 || true
if [[ "$MAIN_RC" -ne 0 ]]; then
  echo "[错误] 主数据导入失败，见 $LOG"
  exit 1
fi

echo "==> 导入 ai_insights..."
CLEAN_AI="/tmp/quantlab_full_ai_clean.sql"
grep -v '^\\restrict' "$AI_SQL" | grep -v '^\\unrestrict' >"$CLEAN_AI"
sudo -u postgres psql -d quantlab -f "$CLEAN_AI" || echo "[警告] ai_insights 导入有问题，可忽略"

echo "==> 修正行情路径（Windows 反斜杠 -> Linux）..."
sudo -u postgres psql -d quantlab -c "
SET search_path TO quantlab, public;
UPDATE market_datasets SET path = replace(path, '\\', '/');
UPDATE market_datasets SET path = 'data/market_data/' || symbol || '_1d.parquet'
  WHERE path NOT LIKE '%/%.parquet';
"

PARQUET_DIR="$INSTALL_DIR/data/market_data"
mkdir -p "$PARQUET_DIR"
if ! ls "$PARQUET_DIR"/*.parquet >/dev/null 2>&1; then
  echo "[警告] $PARQUET_DIR 无 .parquet，请从 Windows 上传 AU/RB/IF_1d.parquet"
fi

if [[ "$SYNC_ENV" == "1" && -f "$WINDOWS_ENV" ]]; then
  echo "==> 同步 Windows .env 密钥（保留 Oracle 的 DATABASE_URL / REDIS_URL）..."
  ORA_DB=$(grep '^DATABASE_URL=' "$INSTALL_DIR/.env" || true)
  ORA_REDIS=$(grep '^REDIS_URL=' "$INSTALL_DIR/.env" || true)
  ORA_CELERY_B=$(grep '^CELERY_BROKER_URL=' "$INSTALL_DIR/.env" || true)
  ORA_CELERY_R=$(grep '^CELERY_RESULT_BACKEND=' "$INSTALL_DIR/.env" || true)
  ORA_MARKET=$(grep '^MARKET_DATA_DIR=' "$INSTALL_DIR/.env" || true)
  cp "$INSTALL_DIR/.env" "$INSTALL_DIR/.env.bak.$(date +%s)"
  grep -E '^(SECRET_KEY|LLM_|AI_|CARD_POOL_|JWT_|ACCESS_TOKEN|CAPTCHA_|RATE_LIMIT_)' "$WINDOWS_ENV" \
    >"$INSTALL_DIR/.env.merge" || true
  {
    echo "APP_ENV=production"
    [[ -n "$ORA_DB" ]] && echo "$ORA_DB"
    [[ -n "$ORA_REDIS" ]] && echo "$ORA_REDIS"
    [[ -n "$ORA_CELERY_B" ]] && echo "$ORA_CELERY_B"
    [[ -n "$ORA_CELERY_R" ]] && echo "$ORA_CELERY_R"
    [[ -n "$ORA_MARKET" ]] && echo "$ORA_MARKET"
    cat "$INSTALL_DIR/.env.merge"
    echo "CELERY_TASK_ALWAYS_EAGER=true"
  } >"$INSTALL_DIR/.env"
  chmod 600 "$INSTALL_DIR/.env"
  rm -f "$INSTALL_DIR/.env.merge"
fi

sudo -u postgres psql -d quantlab -c "
ALTER DATABASE quantlab SET search_path TO quantlab, public;
ALTER ROLE quantlab SET search_path TO quantlab, public;
"

echo "==> 行数核对（精确 COUNT，非 pg_stat 估算）..."
sudo -u postgres psql -d quantlab -c "
SET search_path TO quantlab, public;
ANALYZE;
SELECT 'user_events' AS t, count(*)::bigint AS c FROM user_events
UNION ALL SELECT 'research_nodes', count(*) FROM research_nodes
UNION ALL SELECT 'factors', count(*) FROM factors
UNION ALL SELECT 'users', count(*) FROM users
UNION ALL SELECT 'research_projects', count(*) FROM research_projects
UNION ALL SELECT 'research_templates', count(*) FROM research_templates
UNION ALL SELECT 'backtests', count(*) FROM backtests
UNION ALL SELECT 'validations', count(*) FROM validations
UNION ALL SELECT 'research_reports', count(*) FROM research_reports
UNION ALL SELECT 'tasks', count(*) FROM tasks
ORDER BY c DESC;
"

TPL_COUNT="$(sudo -u postgres psql -tAc "SET search_path TO quantlab, public; SELECT count(*) FROM research_templates" -d quantlab | tr -d ' ')"
if [[ "${TPL_COUNT:-0}" -eq 0 ]]; then
  echo "==> 模板库为空，执行种子补种..."
  sudo -u "${APP_USER:-root}" bash <<EOSU
set -euo pipefail
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
source .venv/bin/activate
set -a && source .env && set +a
python -c "
from backend.app.core.database import SessionLocal
from backend.app.services.template_service import seed_default_templates
from backend.app.services.market_data import seed_real_market_data
from backend.app.services.challenge_service import seed_default_challenge
from backend.app.services.task_service import seed_default_tasks
db = SessionLocal()
try:
    print('templates:', seed_default_templates(db))
    print('market:', seed_real_market_data(db))
    print('challenge:', seed_default_challenge(db))
    print('tasks:', seed_default_tasks(db))
finally:
    db.close()
"
EOSU
fi

echo "==> 启动 quantlab..."
systemctl start quantlab
sleep 2
curl -fsS "http://127.0.0.1:8010/health" && echo ""

echo "全量同步完成。"

#!/usr/bin/env bash
# 补导缺失的业务数据（INSERT 格式，不依赖 COPY）
# 用法: sudo bash /opt/quantlab/scripts/repair-data-oracle.sh
#
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
SQL="${SQL:-/tmp/quantlab_business_inserts_pg10.sql}"

if [[ ! -f "$SQL" ]]; then
  echo "缺少 $SQL"
  echo "Windows: cd C:\\Users\\Administrator\\quantlab && .\\scripts\\export-business-windows.ps1"
  echo "然后 scp 到 /tmp/ 或运行 .\\scripts\\sync-to-oracle.ps1"
  exit 1
fi

systemctl stop quantlab || true

echo "==> 当前精确行数..."
sudo -u postgres psql -d quantlab -c "
SET search_path TO quantlab, public;
SELECT 'factors' t, count(*)::bigint c FROM factors
UNION ALL SELECT 'research_projects', count(*) FROM research_projects
UNION ALL SELECT 'public_reports', count(*) FROM research_reports WHERE is_public
UNION ALL SELECT 'challenges', count(*) FROM challenges;
"

echo "==> 清空业务表（保留 users）..."
sudo -u postgres psql -d quantlab <<'SQL'
SET search_path TO quantlab, public;
TRUNCATE TABLE
  research_edges, research_nodes, research_reports, research_shares,
  submissions, validations, backtests, factors, research_projects,
  research_templates, market_datasets, data_snapshots,
  challenge_progress, challenges, seasons, referrals, redeem_codes,
  subscriptions, user_tasks, user_follows, user_events, tasks,
  ai_insights
CASCADE;
SQL

CLEAN="/tmp/quantlab_inserts_clean.sql"
grep -v '^\\restrict' "$SQL" | grep -v '^\\unrestrict' >"$CLEAN"

echo "==> INSERT 导入..."
LOG="/tmp/quantlab_inserts_restore.log"
sudo -u postgres psql -d quantlab -v ON_ERROR_STOP=1 -f "$CLEAN" >"$LOG" 2>&1 || {
  echo "[错误] 导入失败，最近报错:"
  grep '^ERROR' "$LOG" | tail -20
  echo "完整日志: $LOG"
  exit 1
}

if [[ -f "$INSTALL_DIR/scripts/seed-oracle.sh" ]]; then
  sudo bash "$INSTALL_DIR/scripts/seed-oracle.sh"
else
  echo "==> 平台种子（内联）..."
  sudo -u "${APP_USER:-root}" bash <<EOSU
set -euo pipefail
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
source .venv/bin/activate
set -a && source .env && set +a
python -c "
from backend.app.core.database import SessionLocal
from backend.app.services.template_service import seed_default_templates
from backend.app.services.challenge_service import seed_default_challenge
from backend.app.services.task_service import seed_default_tasks
from backend.app.services.market_data import seed_real_market_data
db = SessionLocal()
try:
    print('templates:', seed_default_templates(db))
    print('challenge:', seed_default_challenge(db))
    print('tasks:', seed_default_tasks(db))
    print('market:', seed_real_market_data(db))
    from backend.app.services.example_studies_service import seed_public_example_studies
    print('examples:', seed_public_example_studies(db))
    from backend.app.services.virtual_community_service import seed_virtual_community
    print('community:', seed_virtual_community(db))
finally:
    db.close()
"
EOSU
fi

echo "==> 导入后精确行数..."
sudo -u postgres psql -d quantlab -c "
SET search_path TO quantlab, public;
ANALYZE;
SELECT 'factors' t, count(*)::bigint c FROM factors
UNION ALL SELECT 'research_projects', count(*) FROM research_projects
UNION ALL SELECT 'research_templates', count(*) FROM research_templates
UNION ALL SELECT 'public_reports', count(*) FROM research_reports WHERE is_public
UNION ALL SELECT 'challenges', count(*) FROM challenges
UNION ALL SELECT 'users', count(*) FROM users
ORDER BY c DESC;
"

FACTORS="$(sudo -u postgres psql -tAc "SET search_path TO quantlab,public; SELECT count(*) FROM factors" -d quantlab | tr -d ' ')"
if [[ "${FACTORS:-0}" -lt 40 ]]; then
  echo "[警告] factors=${FACTORS}，预期约 46。请在本机重新运行 export-business-windows.ps1 后再同步。"
  exit 1
fi

systemctl start quantlab
echo "完成。"

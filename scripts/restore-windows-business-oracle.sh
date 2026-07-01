#!/usr/bin/env bash
# 补导模板库、因子、项目、回测等业务数据（保留已导入的 users）。
#
# 前提:
#   /tmp/quantlab_restore_business_pg10.sql 已上传
#   可选: /opt/quantlab/data/market_data/*.parquet 已从 Windows 复制
#
# 用法:
#   sudo bash /opt/quantlab/scripts/restore-windows-business-oracle.sh
#
set -euo pipefail

DUMP="${DUMP:-/tmp/quantlab_restore_business_pg10.sql}"
INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "请用 sudo 运行"
  exit 1
fi

if [[ ! -f "$DUMP" ]]; then
  echo "找不到 $DUMP"
  echo "请先从 Windows 上传 quantlab_restore_business_pg10.sql 到 /tmp/"
  exit 1
fi

echo "==> 停止 quantlab..."
systemctl stop quantlab || true

echo "==> 清空业务表（保留 users）..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -d quantlab <<'SQL'
SET search_path TO quantlab, public;
TRUNCATE TABLE
  research_edges,
  research_nodes,
  research_reports,
  research_shares,
  submissions,
  validations,
  backtests,
  factors,
  research_projects,
  research_templates,
  market_datasets,
  data_snapshots,
  challenge_progress,
  challenges,
  seasons,
  referrals,
  redeem_codes,
  subscriptions,
  user_tasks,
  user_follows,
  tasks
CASCADE;
SQL

CLEAN="/tmp/quantlab_restore_business_clean.sql"
grep -v '^\\restrict' "$DUMP" | grep -v '^\\unrestrict' >"$CLEAN"

echo "==> 导入业务数据..."
set +e
LOG="/tmp/quantlab_business_restore.log"
sudo -u postgres psql -d quantlab -f "$CLEAN" >"$LOG" 2>&1
set -e
grep -E '^(COPY|ERROR)' "$LOG" | tail -40 || true

echo "==> 统计..."
sudo -u postgres psql -d quantlab -c "
SET search_path TO quantlab, public;
SELECT 'research_templates' AS t, count(*) FROM research_templates
UNION ALL SELECT 'factors', count(*) FROM factors
UNION ALL SELECT 'research_projects', count(*) FROM research_projects
UNION ALL SELECT 'backtests', count(*) FROM backtests
UNION ALL SELECT 'market_datasets', count(*) FROM market_datasets;
"

PARQUET_DIR="$INSTALL_DIR/data/market_data"
if ls "$PARQUET_DIR"/*.parquet >/dev/null 2>&1; then
  echo "==> 行情 Parquet: $(ls "$PARQUET_DIR"/*.parquet | wc -l) 个文件"
else
  echo "[警告] $PARQUET_DIR 下没有 .parquet，回测可能无法跑。请从 Windows 上传 AU_1d/RB_1d/IF_1d.parquet"
fi

echo "==> 启动 quantlab..."
systemctl start quantlab
sleep 2
curl -fsS "http://127.0.0.1:8010/health" && echo "" || true

echo "完成。请刷新 https://q.ziyingke.com/app/ 查看模板库与项目。"

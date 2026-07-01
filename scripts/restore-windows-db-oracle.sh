#!/usr/bin/env bash
# 将 Windows 导出的 quantlab 数据恢复到 Oracle（PG10）上。
#
# 前提:
#   - 备份已传到 /tmp/quantlab_restore_pg10.sql（或传 DUMP_PATH）
#   - 应用已部署在 /opt/quantlab
#
# 用法（Oracle SSH）:
#   sudo bash /opt/quantlab/scripts/restore-windows-db-oracle.sh
#   sudo DUMP_PATH=/tmp/quantlab_restore_pg10.sql bash /opt/quantlab/scripts/restore-windows-db-oracle.sh
#
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
DUMP_PATH="${DUMP_PATH:-/tmp/quantlab_restore_pg10.sql}"
TAIL_DUMP="${TAIL_DUMP:-/tmp/quantlab_restore_tail_pg10.sql}"
APP_USER="${APP_USER:-root}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "请用 sudo 运行"
  exit 1
fi

if [[ ! -f "$DUMP_PATH" ]]; then
  echo "找不到备份: $DUMP_PATH"
  echo "请先从 Windows 上传，例如:"
  echo "  scp -i ~/.ssh/oracle_root quantlab_restore_pg10.sql root@服务器IP:/tmp/"
  exit 1
fi

INIT_SQL="$INSTALL_DIR/infra/db/init.sql"
if [[ ! -f "$INIT_SQL" ]]; then
  echo "找不到 $INIT_SQL"
  exit 1
fi

echo "==> 停止 quantlab..."
systemctl stop quantlab || true

echo "==> 创建 quantlab schema + 扩展 + search_path（与 Windows 一致）..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -d quantlab -f "$INIT_SQL"

echo "==> 将 public 里的业务表迁到 quantlab schema（若存在）..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -d quantlab <<'SQL'
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
      AND tablename NOT IN ('spatial_ref_sys')
  LOOP
    BEGIN
      EXECUTE format('ALTER TABLE public.%I SET SCHEMA quantlab', r.tablename);
      RAISE NOTICE 'moved public.%', r.tablename;
    EXCEPTION
      WHEN duplicate_table THEN
        RAISE NOTICE 'skip public.% (already in quantlab)', r.tablename;
      WHEN OTHERS THEN
        RAISE NOTICE 'skip public.%: %', r.tablename, SQLERRM;
    END;
  END LOOP;
END $$;
SQL

echo "==> 确保 quantlab schema 有表结构..."
TABLE_COUNT="$(sudo -u postgres psql -tAc "SELECT count(*) FROM pg_tables WHERE schemaname='quantlab'" -d quantlab | tr -d ' ')"
if [[ "${TABLE_COUNT:-0}" -eq 0 ]]; then
  sudo -u "$APP_USER" bash <<EOSU
set -euo pipefail
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
source .venv/bin/activate
set -a && source .env && set +a
cd backend && alembic upgrade head
EOSU
else
  echo "quantlab schema 已有 ${TABLE_COUNT} 张表，跳过 alembic"
fi

echo "==> 清空种子/旧数据..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -d quantlab <<'SQL'
SET search_path TO quantlab, public;
TRUNCATE TABLE
  users,
  research_projects,
  research_reports,
  submissions,
  challenges,
  challenge_progress,
  referrals,
  user_follows,
  research_shares,
  redeem_codes,
  user_events,
  tasks,
  user_tasks,
  subscriptions,
  seasons,
  backtests,
  validations,
  factors,
  market_datasets,
  data_snapshots,
  research_nodes,
  research_edges,
  research_templates,
  ai_insights
CASCADE;
SQL

CLEAN_DUMP="/tmp/quantlab_restore_clean.sql"
TAIL_DUMP="${TAIL_DUMP:-}"
echo "==> 清理 PG16 专有语法 -> $CLEAN_DUMP"
grep -v '^\\restrict' "$DUMP_PATH" | grep -v '^\\unrestrict' >"$CLEAN_DUMP"

echo "==> 导入 Windows 数据（users 等；ai_insights 含换行可能失败，可忽略）..."
set +e
IMPORT_LOG="/tmp/quantlab_restore.log"
sudo -u postgres psql -d quantlab -f "$CLEAN_DUMP" >"$IMPORT_LOG" 2>&1
IMPORT_RC=$?
set -e
grep -E '^(COPY|ERROR)' "$IMPORT_LOG" | tail -30 || true
if [[ "$IMPORT_RC" -ne 0 ]]; then
  echo "[提示] 全量导入未完全成功（常见: ai_insights 多行文本）。继续补导剩余表..."
fi

if [[ -f "$TAIL_DUMP" ]]; then
  echo "==> 补导剩余表（跳过 users / ai_insights）..."
  CLEAN_TAIL="/tmp/quantlab_restore_tail_clean.sql"
  grep -v '^\\restrict' "$TAIL_DUMP" | grep -v '^\\unrestrict' >"$CLEAN_TAIL"
  # alembic_version 在 Oracle 上已由迁移写入，跳过避免 duplicate key 中断后续 COPY
  awk '/^COPY quantlab\.alembic_version /,/^\\\./ {next} {print}' "$CLEAN_TAIL" \
    >/tmp/quantlab_restore_tail_no_alembic.sql
  set +e
  sudo -u postgres psql -d quantlab -f /tmp/quantlab_restore_tail_no_alembic.sql \
    >"$IMPORT_LOG.tail" 2>&1
  set -e
  grep -E '^(COPY|ERROR)' "$IMPORT_LOG.tail" | tail -30 || true
fi

USER_COUNT="$(sudo -u postgres psql -tAc "SET search_path TO quantlab, public; SELECT count(*) FROM users" -d quantlab | tr -d ' ')"
PROJ_COUNT="$(sudo -u postgres psql -tAc "SET search_path TO quantlab, public; SELECT count(*) FROM research_projects" -d quantlab | tr -d ' ')"
echo "==> users 行数: ${USER_COUNT}, research_projects: ${PROJ_COUNT}"

if [[ "${USER_COUNT:-0}" -lt 1 ]]; then
  echo "错误: 导入后 users 仍为空，请检查上方 psql 报错"
  exit 1
fi

echo "==> 启动 quantlab..."
systemctl start quantlab
sleep 2
curl -fsS "http://127.0.0.1:8010/health" && echo "" || echo "健康检查失败，请: journalctl -u quantlab -n 50 --no-pager"

echo "完成。请用旧账号密码在 https://q.ziyingke.com/app/ 登录验证。"

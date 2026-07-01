#!/usr/bin/env bash
# 修复 PostgreSQL 10 上 quantlab 用户 127.0.0.1 密码登录 (Ident failed)
set -euo pipefail
ENV_FILE="${1:-/opt/quantlab/.env}"
PG_HBA=/var/lib/pgsql/data/pg_hba.conf

if [[ ! -f "$ENV_FILE" ]]; then
  echo "找不到 $ENV_FILE"
  exit 1
fi
DB_PASS=$(grep '^DATABASE_URL=' "$ENV_FILE" | sed -n 's#.*quantlab:\([^@]*\)@.*#\1#p')
if [[ -z "$DB_PASS" ]]; then
  echo "无法从 DATABASE_URL 解析密码"
  exit 1
fi

if ! grep -q 'quantlab.*127.0.0.1' "$PG_HBA"; then
  LINE='host    quantlab    quantlab    127.0.0.1/32    md5'
  if grep -q '^host.*127.0.0.1/32.*ident' "$PG_HBA"; then
    sed -i "/^host.*127.0.0.1\/32.*ident/i ${LINE}" "$PG_HBA"
  else
    echo "$LINE" >>"$PG_HBA"
  fi
  echo "已写入 pg_hba.conf"
fi

sudo -u postgres psql -v ON_ERROR_STOP=1 -c "ALTER USER quantlab WITH PASSWORD '${DB_PASS}';"
systemctl reload postgresql || systemctl restart postgresql
echo "PostgreSQL 已重载，quantlab 密码已同步 .env"

#!/usr/bin/env bash
# QuantLab — 与现有网站共存的安全部署（不碰已有 Nginx 站点配置）
#
# 原则:
#   - 独立目录 /opt/quantlab
#   - 独立数据库 quantlab（只 CREATE，不 DROP 别的库）
#   - Redis 用 10/11/12 号库，避免和别的应用抢 0/1/2
#   - 只监听 127.0.0.1:QUANTLAB_PORT（默认 8010）
#   - 独立 systemd: quantlab.service
#   - 不改已有 nginx/caddy 配置；可选单独加 q.ziyingke.com
#
# 用法:
#   bash scripts/preflight-coexist.sh
#   sudo QUANTLAB_PORT=8010 bash scripts/deploy-coexist.sh
#
set -euo pipefail

REPO_URL="${REPO_URL:-git@github.com:max1949/quantlab.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
if id ubuntu &>/dev/null; then
  APP_USER="${APP_USER:-ubuntu}"
else
  APP_USER="${APP_USER:-root}"
fi
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-}"
QUANTLAB_PORT="${QUANTLAB_PORT:-8010}"
# 已有 Postgres/Redis 时设为 1，跳过 apt 安装
SKIP_INSTALL_PG="${SKIP_INSTALL_PG:-0}"
SKIP_INSTALL_REDIS="${SKIP_INSTALL_REDIS:-0}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "请用 sudo 运行"
  exit 1
fi

port_busy() {
  ss -tln 2>/dev/null | grep -q ":$1 "
}

if port_busy "$QUANTLAB_PORT"; then
  echo "端口 ${QUANTLAB_PORT} 已被占用。请换端口，例如:"
  echo "  sudo QUANTLAB_PORT=8011 bash $0"
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
PG_SERVICE="postgresql"
REDIS_SERVICE="redis-server"

install_deps_apt() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  local pkgs=(git curl python3 python3-venv python3-pip build-essential libpq-dev)
  if [[ "$SKIP_INSTALL_PG" != "1" ]] && ! command -v psql >/dev/null 2>&1; then
    pkgs+=(postgresql postgresql-contrib)
  fi
  if [[ "$SKIP_INSTALL_REDIS" != "1" ]] && ! command -v redis-cli >/dev/null 2>&1; then
    pkgs+=(redis-server)
  fi
  apt-get install -y -qq "${pkgs[@]}"
  PG_SERVICE=postgresql
  REDIS_SERVICE=redis-server
}

install_deps_dnf() {
  local mgr=$1
  $mgr install -y git curl gcc make openssl-devel
  # OL8 默认 python3 常为 3.6，QuantLab 需要 3.9+
  if $mgr install -y python39 python39-pip python39-devel 2>/dev/null; then
    PYTHON_BIN=python3.9
  elif $mgr install -y python3.11 python3.11-pip python3.11-devel 2>/dev/null; then
    PYTHON_BIN=python3.11
  else
    $mgr install -y python3 python3-pip python3-devel
    PYTHON_BIN=python3
  fi
  if ! "$PYTHON_BIN" -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    echo "错误: 需要 Python 3.9+，当前: $($PYTHON_BIN --version 2>&1)"
    echo "请执行: dnf install -y python39 python39-pip python39-devel"
    exit 1
  fi
  if [[ "$SKIP_INSTALL_PG" != "1" ]] && ! command -v psql >/dev/null 2>&1; then
    $mgr module enable -y postgresql:13 2>/dev/null || $mgr module enable -y postgresql:15 2>/dev/null || true
    $mgr install -y postgresql-server postgresql postgresql-contrib
    if command -v postgresql-setup >/dev/null 2>&1; then
      postgresql-setup --initdb 2>/dev/null || true
    fi
    PG_SERVICE=postgresql
  fi
  if [[ "$SKIP_INSTALL_REDIS" != "1" ]] && ! command -v redis-cli >/dev/null 2>&1; then
    $mgr install -y redis
    REDIS_SERVICE=redis
  fi
  $mgr install -y postgresql-devel 2>/dev/null || $mgr install -y libpq-devel 2>/dev/null || true
}

ensure_pg_local_auth() {
  local pg_hba=""
  for f in /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/*/data/pg_hba.conf; do
    [[ -f "$f" ]] && pg_hba="$f" && break
  done
  if [[ -z "$pg_hba" ]]; then
    return
  fi
  if grep -q 'quantlab.*127.0.0.1' "$pg_hba"; then
    return
  fi
  local line='host    quantlab    quantlab    127.0.0.1/32    md5'
  if grep -q '^host.*127.0.0.1/32.*ident' "$pg_hba"; then
    sed -i "/^host.*127.0.0.1\/32.*ident/i ${line}" "$pg_hba"
  else
    echo "$line" >>"$pg_hba"
  fi
  systemctl reload "$PG_SERVICE" 2>/dev/null || systemctl restart "$PG_SERVICE" 2>/dev/null || true
}

echo "==> 安装系统依赖（不启动/不重载其他网站）..."
if command -v apt-get >/dev/null 2>&1; then
  install_deps_apt
elif command -v dnf >/dev/null 2>&1; then
  install_deps_dnf dnf
elif command -v yum >/dev/null 2>&1; then
  install_deps_dnf yum
else
  echo "未找到 apt-get / dnf / yum，请手动安装 git python3 postgresql redis 后重试"
  exit 1
fi

if [[ "$SKIP_INSTALL_PG" != "1" ]] && systemctl list-unit-files 2>/dev/null | grep -q "^${PG_SERVICE}.service"; then
  systemctl enable "$PG_SERVICE" 2>/dev/null || true
  systemctl start "$PG_SERVICE" || true
  sleep 2
  if ! sudo -u postgres psql -tAc "SELECT 1" >/dev/null 2>&1; then
    echo "PostgreSQL 未就绪，尝试初始化..."
    postgresql-setup --initdb 2>/dev/null || true
    systemctl restart "$PG_SERVICE" || true
    sleep 2
  fi
  if ! sudo -u postgres psql -tAc "SELECT 1" >/dev/null 2>&1; then
    echo "错误: PostgreSQL 仍无法连接。请先手动执行:"
    echo "  dnf install -y postgresql-server postgresql"
    echo "  postgresql-setup --initdb"
    echo "  systemctl enable --now postgresql"
    exit 1
  fi
  ensure_pg_local_auth
fi
if [[ "$SKIP_INSTALL_REDIS" != "1" ]] && systemctl list-unit-files 2>/dev/null | grep -q "^${REDIS_SERVICE}.service"; then
  systemctl enable "$REDIS_SERVICE" 2>/dev/null || true
  systemctl start "$REDIS_SERVICE" || true
fi

echo "==> PostgreSQL: 仅新建 quantlab 库/用户..."
DB_PASS="${QUANTLAB_DB_PASS:-}"
if [[ -z "$DB_PASS" ]]; then
  if [[ -f "$INSTALL_DIR/.env" ]] && grep -q '^DATABASE_URL=' "$INSTALL_DIR/.env"; then
    echo "保留已有 DATABASE_URL"
    DB_PASS="(unchanged)"
  else
    DB_PASS="$(openssl rand -hex 16)"
    sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'quantlab') THEN
    CREATE ROLE quantlab LOGIN PASSWORD '${DB_PASS}';
  END IF;
END \$\$;
SELECT 'CREATE DATABASE quantlab OWNER quantlab'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'quantlab')\gexec
GRANT ALL PRIVILEGES ON DATABASE quantlab TO quantlab;
ALTER USER quantlab WITH PASSWORD '${DB_PASS}';
SQL
    ensure_pg_local_auth
  fi
fi

echo "==> 拉取代码到 ${INSTALL_DIR}..."
mkdir -p "$(dirname "$INSTALL_DIR")"
if [[ -d "$INSTALL_DIR/.git" ]]; then
  sudo -u "$APP_USER" env GIT_SSH_COMMAND="$GIT_SSH_COMMAND" git -C "$INSTALL_DIR" pull --ff-only
else
  sudo -u "$APP_USER" env GIT_SSH_COMMAND="$GIT_SSH_COMMAND" git clone "$REPO_URL" "$INSTALL_DIR"
fi
chown -R "$APP_USER:$APP_USER" "$INSTALL_DIR"

echo "==> Python 虚拟环境 (${PYTHON_BIN})..."
sudo -u "$APP_USER" bash <<EOSU
set -euo pipefail
cd "$INSTALL_DIR"
${PYTHON_BIN} -m venv .venv
source .venv/bin/activate
pip install -q -U pip wheel
pip install -q -r backend/requirements.txt
EOSU

if [[ ! -f "$INSTALL_DIR/.env" ]]; then
  SECRET_KEY="$(openssl rand -hex 32)"
  cat >"$INSTALL_DIR/.env" <<ENV
APP_ENV=production
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql+psycopg://quantlab:${DB_PASS}@127.0.0.1:5432/quantlab
REDIS_URL=redis://127.0.0.1:6379/10
CELERY_BROKER_URL=redis://127.0.0.1:6379/11
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/12
CELERY_TASK_ALWAYS_EAGER=true
MARKET_DATA_DIR=${INSTALL_DIR}/data/market_data
CAPTCHA_DISABLED=false
RATE_LIMIT_DISABLED=false
ENV
  chown "$APP_USER:$APP_USER" "$INSTALL_DIR/.env"
  chmod 600 "$INSTALL_DIR/.env"
else
  echo "保留已有 .env"
fi

echo "==> 迁移 + 种子（仅 quantlab 库）..."
sudo -u "$APP_USER" bash <<EOSU
set -euo pipefail
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
source .venv/bin/activate
set -a && source .env && set +a
cd backend && alembic upgrade head
cd "$INSTALL_DIR"
python -c "
from backend.app.core.database import SessionLocal
from backend.app.services.template_service import seed_default_templates
from backend.app.services.market_data import seed_real_market_data
from backend.app.services.challenge_service import seed_default_challenge
db = SessionLocal()
try:
    print('templates:', seed_default_templates(db))
    print('market:', seed_real_market_data(db))
    print('challenge:', seed_default_challenge(db))
finally:
    db.close()
"
EOSU

echo "==> systemd 服务 quantlab（仅本机 ${QUANTLAB_PORT}）..."
cat >/etc/systemd/system/quantlab.service <<UNIT
[Unit]
Description=QuantLab AI backend (coexist)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${INSTALL_DIR}
Environment=PYTHONPATH=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port ${QUANTLAB_PORT}
Restart=on-failure
RestartSec=5
# 资源上限，避免拖垮同机其他站（可按机器配置调整）
MemoryMax=2G
CPUQuota=150%

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable quantlab
systemctl restart quantlab

sleep 2
if curl -fsS "http://127.0.0.1:${QUANTLAB_PORT}/health" >/dev/null; then
  echo ""
  echo "============================================"
  echo " QuantLab 共存部署成功"
  echo " 健康检查: http://127.0.0.1:${QUANTLAB_PORT}/health"
  echo ""
  echo " 对外暴露（二选一，不动现有站）:"
  echo "  A) Cloudflare Tunnel 新增 hostname q.ziyingke.com -> 127.0.0.1:${QUANTLAB_PORT}"
  echo "  B) Nginx 单独加 server_name q.ziyingke.com（见 docs/oracle-coexist.md）"
  echo ""
  echo " 回滚: sudo systemctl stop quantlab && sudo systemctl disable quantlab"
  echo "============================================"
else
  echo "服务已安装但健康检查失败，请执行: journalctl -u quantlab -n 50 --no-pager"
  exit 1
fi

#!/usr/bin/env bash
# QuantLab AI — Oracle Cloud Ubuntu (ARM) 一键部署
# 在服务器上运行（已 SSH 登录为 ubuntu 用户）:
#   curl -fsSL https://raw.githubusercontent.com/max1949/quantlab/master/scripts/deploy-oracle-ubuntu.sh | bash
# 或克隆仓库后:
#   sudo bash scripts/deploy-oracle-ubuntu.sh
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/max1949/quantlab.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
APP_USER="${APP_USER:-ubuntu}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "请用 sudo 运行: sudo bash $0"
  exit 1
fi

echo "==> 安装系统依赖..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl python3 python3-venv python3-pip \
  postgresql postgresql-contrib redis-server build-essential libpq-dev

systemctl enable --now postgresql redis-server

echo "==> 配置 PostgreSQL..."
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
SQL

echo "==> 拉取代码..."
mkdir -p "$(dirname "$INSTALL_DIR")"
if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$INSTALL_DIR"
fi
chown -R "$APP_USER:$APP_USER" "$INSTALL_DIR"

echo "==> Python 虚拟环境 + 依赖..."
sudo -u "$APP_USER" bash <<EOSU
set -euo pipefail
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -U pip wheel
pip install -q -r backend/requirements.txt
EOSU

SECRET_KEY="$(openssl rand -hex 32)"
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
  cat >"$INSTALL_DIR/.env" <<ENV
APP_ENV=production
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql+psycopg://quantlab:${DB_PASS}@127.0.0.1:5432/quantlab
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
CELERY_TASK_ALWAYS_EAGER=true
MARKET_DATA_DIR=${INSTALL_DIR}/data/market_data
CAPTCHA_DISABLED=false
RATE_LIMIT_DISABLED=false
ENV
  chown "$APP_USER:$APP_USER" "$INSTALL_DIR/.env"
  chmod 600 "$INSTALL_DIR/.env"
  echo "已生成 $INSTALL_DIR/.env — 请稍后补上 LLM_API_KEY、CARD_POOL_* 等"
else
  echo "保留已有 .env"
fi

echo "==> 数据库迁移 + 种子数据..."
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

echo "==> systemd 服务..."
cat >/etc/systemd/system/quantlab.service <<UNIT
[Unit]
Description=QuantLab AI backend
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${INSTALL_DIR}
Environment=PYTHONPATH=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now quantlab

echo ""
echo "============================================"
echo " 部署完成"
echo " 本机健康检查: curl http://127.0.0.1:8000/health"
echo " 下一步: 安装 cloudflared 并把隧道指到本机 :8000"
echo " 然后改 Cloudflare DNS 或复用现有 quantlab 隧道配置"
echo "============================================"

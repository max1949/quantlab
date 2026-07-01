#!/usr/bin/env bash
# Oracle 上补种平台默认数据（模板 / 挑战 / 任务 / 行情索引）
# 用法: sudo bash /opt/quantlab/scripts/seed-oracle.sh
#
set -euo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
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
finally:
    db.close()
"

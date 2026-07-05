#!/usr/bin/env bash
# 注册后 ≥3 天仍未开始研究的用户 — 每日回流邮件 (cron: 09:30)
set -euo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
source .venv/bin/activate
set -a && source .env && set +a
python -c "
from backend.app.core.database import SessionLocal
from backend.app.services import revisit_email_service as res
db = SessionLocal()
try:
    print(res.run_scheduled_revisit_batch(db))
finally:
    db.close()
"

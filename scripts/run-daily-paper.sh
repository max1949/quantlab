#!/usr/bin/env bash
# 每日纸面跟踪快照 (cron: 工作日 18:30)
set -euo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
source .venv/bin/activate
set -a && source .env && set +a
python -c "
from backend.app.core.database import SessionLocal
from backend.app.services import paper_tracking_service as pts
db = SessionLocal()
try:
    print(pts.run_daily_paper_batch(db))
finally:
    db.close()
"

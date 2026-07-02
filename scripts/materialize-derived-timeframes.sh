#!/usr/bin/env bash
# 从已有 1m Parquet 派生 5m/15m/30m/1h 中频周期 (幂等)
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
source "$INSTALL_DIR/.venv/bin/activate"
set -a && source "$INSTALL_DIR/.env" && set +a

python -c "
from backend.app.core.database import SessionLocal
from backend.app.services.market_data import materialize_derived_timeframes
db = SessionLocal()
try:
    print(materialize_derived_timeframes(db))
finally:
    db.close()
"

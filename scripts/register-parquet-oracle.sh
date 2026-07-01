#!/usr/bin/env bash
# 扫描 /opt/quantlab/data/market_data/*.parquet 并更新 PG 索引 (不上传后必须跑)
set -euo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
source .venv/bin/activate
set -a && source .env && set +a
python -c "
from backend.app.core.database import SessionLocal
from backend.app.services.vnpy_mongo_import import register_all_parquet
db = SessionLocal()
try:
    print(register_all_parquet(db))
finally:
    db.close()
"

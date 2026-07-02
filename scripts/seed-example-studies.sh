#!/usr/bin/env bash
# 播种 3–5 份公开示例研究 (Feed / SEO)
# 用法: 在仓库根目录  bash scripts/seed-example-studies.sh
#       或 Oracle: sudo bash /opt/quantlab/scripts/seed-example-studies.sh
set -euo pipefail
INSTALL_DIR="${INSTALL_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR"
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi
if [[ -f .env ]]; then
  set -a && source .env && set +a
fi
python -c "
from backend.app.core.database import SessionLocal
from backend.app.services.example_studies_service import seed_public_example_studies

db = SessionLocal()
try:
    print(seed_public_example_studies(db))
finally:
    db.close()
"

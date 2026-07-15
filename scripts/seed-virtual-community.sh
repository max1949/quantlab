#!/usr/bin/env bash
# 播种虚拟社区人气数据 (广场 / 榜单 / 关注)
# 用法: bash scripts/seed-virtual-community.sh
#       Oracle: sudo bash /opt/quantlab/scripts/seed-virtual-community.sh
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
from backend.app.services.virtual_community_service import seed_virtual_community

db = SessionLocal()
try:
    print('examples:', seed_public_example_studies(db))
    print('community:', seed_virtual_community(db))
finally:
    db.close()
"

#!/bin/bash
set -euo pipefail
cd /srv/quantlab
set -a; source .env; set +a
export PYTHONPATH=/srv/quantlab
OUT=$(.venv/bin/python - <<'PY'
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.auth.security import create_access_token
from sqlalchemy import select

db = SessionLocal()
user = db.execute(select(User).where(User.username == "wen")).scalar_one_or_none()
if user is None:
    user = db.execute(select(User).limit(1)).scalar_one()
token = create_access_token(subject=str(user.id))
print(user.username)
print(token)
db.close()
PY
)
USER=$(echo "$OUT" | sed -n '1p')
TOKEN=$(echo "$OUT" | sed -n '2p')
echo "USER=$USER"
code=$(curl -s -o /tmp/ai_out.json -w "%{http_code}" -X POST http://127.0.0.1:8010/api/v1/ai/strategy-builder \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"text":"欧元美元15分钟。EMA20上穿EMA60。每笔最多亏0.5%。","confirm":false,"run_backtest":false}')
echo "HTTP=$code"
python3 - <<'PY'
import json
d=json.load(open("/tmp/ai_out.json"))
if isinstance(d, dict):
    print("keys", sorted(d.keys())[:20])
    print("detail", d.get("detail"))
    print("live_denied", d.get("live_denied"))
    b = d.get("builder") or {}
    print("builder_keys", list(b.keys())[:12])
    print("ambiguous", b.get("ambiguous"))
    ds = (b.get("draft_spec") or {})
    print("strategy_name", ((ds.get("strategy") or {}).get("name")))
else:
    print(d)
PY

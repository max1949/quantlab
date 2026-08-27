#!/usr/bin/env python3
"""Post-deploy verify: flags + AI builder HTTP with real user JWT."""
from __future__ import annotations

import os
import sys

os.chdir("/srv/quantlab")
sys.path.insert(0, "/srv/quantlab")

from backend.app.core.config import get_settings
from backend.app.core.database import SessionLocal
from backend.app.auth.security import create_access_token
from backend.app.models.user import User
from engine.ai.strategy_builder import build_strategy_from_chinese
from sqlalchemy import select
import httpx

get_settings.cache_clear()
s = get_settings()
assert s.quantlab_ai_strategy_builder is True, s.quantlab_ai_strategy_builder
assert s.quantlab_live is False
assert s.quantlab_sandbox is True
print("FLAGS_OK AI_BUILDER=ON LIVE=OFF SANDBOX=ON")

r = build_strategy_from_chinese("欧元美元15分钟 EMA10上穿EMA20")
assert r.draft_spec is not None, r
print("RULE_ENGINE_OK instrument=", r.draft_spec.get("market", {}).get("instrument"))

db = SessionLocal()
user = db.execute(select(User).where(User.username == "ziyingke")).scalar_one_or_none()
if user is None:
    user = db.execute(select(User).limit(1)).scalar_one()
token = create_access_token(str(user.id))
db.close()

resp = httpx.post(
    "http://127.0.0.1:8010/api/v1/ai/strategy-builder",
    headers={"Authorization": f"Bearer {token}"},
    json={"text": "欧元美元15分钟 EMA10上穿EMA20", "confirm": False, "run_backtest": False},
    timeout=60.0,
)
print("HTTP", resp.status_code)
print(resp.text[:500])
assert resp.status_code == 200, resp.text
body = resp.json()
assert body.get("live_denied") is True
assert body.get("builder", {}).get("draft_spec") or body.get("builder", {}).get("questions")
print("AI_STRATEGY_BUILDER_HTTP=PASS user=", user.username)

# billing status stripe fields
resp2 = httpx.get(
    "http://127.0.0.1:8010/api/v1/billing/me",
    headers={"Authorization": f"Bearer {token}"},
    timeout=30.0,
)
print("BILLING_ME", resp2.status_code, list(resp2.json().keys())[:12] if resp2.status_code == 200 else resp2.text[:200])
print("VERIFY=PASS")

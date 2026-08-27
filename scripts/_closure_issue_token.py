#!/usr/bin/env python3
"""Issue JWT for browser injection (prod/local). Prints username\\ntoken only."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = Path("/srv/quantlab")
work = PROD if (PROD / ".env").is_file() else ROOT
os.chdir(work)
sys.path.insert(0, str(work))

def _load(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load(work / ".env")

from sqlalchemy import select
from backend.app.auth.security import create_access_token
from backend.app.core.database import SessionLocal
from backend.app.models.user import User

uname = os.environ.get("CLOSURE_USER", "ziyingke")
db = SessionLocal()
user = db.execute(select(User).where(User.username == uname)).scalar_one_or_none()
if user is None:
    raise SystemExit(f"user not found: {uname}")
print(user.username)
print(create_access_token(subject=str(user.id)))
db.close()

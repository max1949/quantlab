#!/usr/bin/env python3
"""Read-only challenge progress probe on production."""
from __future__ import annotations

import os
import sys

os.chdir("/srv/quantlab")
sys.path.insert(0, "/srv/quantlab")

from sqlalchemy import select, text

from backend.app.core.database import SessionLocal
from backend.app.models.challenge import Challenge
from backend.app.services.challenge_service import DEFAULT_MILESTONES

db = SessionLocal()
print("MILESTONES")
for m in DEFAULT_MILESTONES:
    print(f"  day={m['day']} code={m['code']} check={m['check']} pts={m['reward_points']}")

chs = db.execute(select(Challenge)).scalars().all()
for c in chs:
    print(f"CHALLENGE code={c.code} title={c.title} milestones={len(c.milestones or [])}")

rows = db.execute(
    text(
        """
        SELECT u.username,
               c.code,
               COALESCE(jsonb_array_length(to_jsonb(cp.completed)), 0) AS done_n,
               cp.completed,
               cp.rewarded,
               cp.certificate_code,
               cp.completed_at
        FROM quantlab.challenge_progress cp
        JOIN quantlab.users u ON u.id = cp.user_id
        JOIN quantlab.challenges c ON c.id = cp.challenge_id
        ORDER BY done_n DESC
        LIMIT 20
        """
    )
).fetchall()
print("TOP_PROGRESS")
for r in rows:
    print(dict(r._mapping))

# Find users at 7/8
rows7 = db.execute(
    text(
        """
        SELECT u.username, cp.completed, cp.rewarded
        FROM quantlab.challenge_progress cp
        JOIN quantlab.users u ON u.id = cp.user_id
        WHERE jsonb_array_length(to_jsonb(cp.completed)) = 7
        LIMIT 10
        """
    )
).fetchall()
print("AT_7_OF_8")
for r in rows7:
    print(dict(r._mapping))

db.close()

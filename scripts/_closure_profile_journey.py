#!/usr/bin/env bash
set -euo pipefail
cd /srv/quantlab
set -a; source .env; set +a
export PYTHONPATH=/srv/quantlab
.venv/bin/python <<'PY'
import time
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.services import challenge_service, onboarding_service as obs
from backend.app.services import research_quality_service as rqs
from backend.app.services import leaderboard_service as lbs

db = SessionLocal()
user = db.query(User).filter(User.username == "ziyingke").one()

def t(label, fn):
    a = time.perf_counter()
    r = fn()
    b = time.perf_counter()
    print(f"{label:40s} {b-a:7.3f}s")
    return r

t("user_paper_mastery_counts", lambda: rqs.user_paper_mastery_counts(db, user.id))
t("paper_mastery_board_context", lambda: lbs.paper_mastery_board_context(db, user.id))
t("_any_factor_paper_graduated", lambda: challenge_service._any_factor_paper_graduated(db, user.id))
t("evaluate", lambda: challenge_service.evaluate(db, user, "30d-research"))
t("_mastery_goal_payload", lambda: obs._mastery_goal_payload(db, user, "zh"))
t("research_journey", lambda: obs.research_journey(db, user, "zh"))
db.close()
PY

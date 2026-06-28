"""API v1 路由汇聚点。

各模块路由 (auth / users / tasks / projects / factors / backtests /
validations / seasons / leaderboard / ai) 在后续 Sprint 中实现后, 在此 include。
Sprint 1: 暴露 ping + 用户系统 (auth / users)。
"""

from fastapi import APIRouter

from backend.app.api.v1.routes import (
    ai,
    auth,
    backtests,
    challenges,
    competition,
    events,
    factors,
    leaderboards,
    me,
    onboarding,
    projects,
    public,
    research,
    researchers,
    tasks,
    users,
    validations,
)

api_router = APIRouter()


@api_router.get("/ping", tags=["system"])
def ping() -> dict:
    return {"pong": True}


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["academy"])
api_router.include_router(factors.router, prefix="/factors", tags=["factor-lab"])
api_router.include_router(backtests.router)  # /datasets · /backtests
api_router.include_router(validations.router, prefix="/validations", tags=["validation"])
api_router.include_router(competition.router, prefix="/seasons", tags=["competition"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(projects.router, prefix="/projects", tags=["project"])
api_router.include_router(researchers.router, prefix="/researchers", tags=["researcher"])
api_router.include_router(challenges.router, prefix="/challenges", tags=["challenge"])

# Growth OS (Sprint 9A)
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(me.router, prefix="/me", tags=["me"])
api_router.include_router(leaderboards.router, prefix="/leaderboards", tags=["leaderboard"])
api_router.include_router(events.router, prefix="/events", tags=["growth"])
api_router.include_router(public.router, prefix="/share", tags=["public"])

# 后续 Sprint 继续在此挂载: execution-adapter (vn.py/QMT, Phase 3) / ...

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
    competition,
    factors,
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

# 后续 Sprint 继续在此挂载: simulated-trading / ...

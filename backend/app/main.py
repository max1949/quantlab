"""FastAPI 应用入口。

职责: 仅做装配 (创建 app、挂载路由、健康检查)。
不在此处编写业务逻辑 —— API 进程不做重计算, 重计算走 Celery Worker。
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1 import api_router
from backend.app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="QuantLab AI —— AI 量化研究员孵化与因子研究平台",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict:
    """存活探针。"""
    return {"status": "ok", "env": settings.app_env}


# 极简前端单页演示 (Sprint 8): 走完整 Research OS 闭环。
_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if (_FRONTEND_DIR / "index.html").exists():
    @app.get("/", include_in_schema=False)
    def _root() -> RedirectResponse:
        return RedirectResponse(url="/app/")

    app.mount("/app", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")

"""FastAPI 应用入口。

职责: 仅做装配 (创建 app、挂载路由、健康检查)。
不在此处编写业务逻辑 —— API 进程不做重计算, 重计算走 Celery Worker。
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1 import api_router
from backend.app.core.config import get_settings
from backend.app.web import share_preview

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="QuantLab AI —— AI 量化研究员孵化与因子研究平台",
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(api_router, prefix="/api/v1")
app.include_router(share_preview.router)


@app.get("/robots.txt", include_in_schema=False, response_class=PlainTextResponse)
def robots_txt() -> str:
    return "User-agent: *\nAllow: /app/\nAllow: /share/\n"


@app.get("/health", tags=["system"])
def health() -> dict:
    """存活探针。"""
    return {"status": "ok", "env": settings.app_env}


_REPO_ROOT = Path(__file__).resolve().parents[2]
_REACT_DIST = _REPO_ROOT / "frontend-react" / "dist"
_LEGACY_FRONTEND_DIR = _REPO_ROOT / "frontend"

_SPA_SHORTCUTS = frozenset({
    "/login",
    "/register",
    "/feed",
    "/pricing",
    "/leaderboards",
    "/templates",
    "/projects",
    "/onboarding",
    "/challenges",
    "/me",
})


@app.middleware("http")
async def spa_path_shortcuts(request: Request, call_next):
    """Redirect /login etc. to /app/login (SPA base path)."""
    if request.method == "GET":
        path = request.url.path
        skip = (
            path.startswith(("/api/", "/app", "/app-legacy", "/docs", "/openapi.json"))
            or path == "/health"
        )
        if not skip:
            if path == "/":
                return RedirectResponse(url="/app/")
            if path in _SPA_SHORTCUTS:
                return RedirectResponse(url=f"/app{path}")
    return await call_next(request)


@app.get("/", include_in_schema=False)
def _root() -> RedirectResponse:
    return RedirectResponse(url="/app/")


# Sprint 9B: React SPA (Vite 构建产物) 挂在 /app。
# SPA 路由 (如 /app/projects/123) 刷新需回退到 index.html (html=True 已支持顶层,
# 这里再加一个 catch-all 兜底深层路由)。
if (_REACT_DIST / "index.html").exists():
    _spa_index = _REACT_DIST / "index.html"

    @app.get("/app/{full_path:path}", include_in_schema=False)
    def _spa_fallback(full_path: str) -> FileResponse:
        candidate = _REACT_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_spa_index))

    app.mount("/app", StaticFiles(directory=str(_REACT_DIST), html=True), name="frontend")

# Sprint 8 旧版极简 demo 保留在 /app-legacy。
if (_LEGACY_FRONTEND_DIR / "index.html").exists():
    app.mount(
        "/app-legacy",
        StaticFiles(directory=str(_LEGACY_FRONTEND_DIR), html=True),
        name="frontend-legacy",
    )

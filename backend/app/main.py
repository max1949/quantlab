"""FastAPI 应用入口。

职责: 仅做装配 (创建 app、挂载路由、健康检查)。
不在此处编写业务逻辑 —— API 进程不做重计算, 重计算走 Celery Worker。
"""

from pathlib import Path

from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.app.api.v1 import api_router
from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.services import health_service
from backend.app.web import report_preview, share_preview

settings = get_settings()
if settings.app_env == "production" and settings.secret_key == "change-me-in-production":
    raise RuntimeError("SECRET_KEY must be set in production")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="QuantLab AI —— AI 量化研究员孵化与因子研究平台",
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None if settings.app_env == "production" else "/redoc",
    openapi_url=None if settings.app_env == "production" else "/openapi.json",
)


_CACHEABLE_API_PREFIXES = (
    "/api/v1/public/",
    "/api/v1/factors/templates",
    "/api/v1/factors/formula/help",
    "/api/v1/factors/python/help",
    "/api/v1/billing/plans",
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        if any(request.url.path.startswith(p) for p in _CACHEABLE_API_PREFIXES):
            response.headers["Cache-Control"] = "public, max-age=300"
        else:
            response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(api_router, prefix="/api/v1")
app.include_router(share_preview.router)
app.include_router(report_preview.router)


@app.get("/robots.txt", include_in_schema=False, response_class=PlainTextResponse)
def robots_txt(request: Request) -> str:
    origin = (settings.public_base_url or str(request.base_url)).rstrip("/")
    return (
        "User-agent: *\n"
        "Allow: /app/\n"
        "Allow: /share/\n"
        "Allow: /reports/\n"
        f"Sitemap: {origin}/sitemap.xml\n"
    )


@app.get("/health", tags=["system"])
def health() -> dict:
    """存活探针。"""
    if settings.app_env == "production":
        return {"status": "ok"}
    return {"status": "ok", "env": settings.app_env}


@app.get("/health/ready", tags=["system"])
def health_ready(db: Annotated[Session, Depends(get_db)]) -> dict:
    """就绪探针 — DB / Redis (Celery 仅作参考, 不阻塞 ready)。"""
    body = health_service.readiness(db)
    if body["status"] != "ready":
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=body)
    return body


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
            or path.startswith("/health/")
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

"""公开研究报告的 SEO 预览 (OG / JSON-LD) + sitemap。

访客/爬虫访问 /reports/{id} 时:
- 报告已公开: 返回带标题、摘要、结构化数据的可索引 HTML, 并跳转进 SPA (/app/reports/{id})。
- 未公开/不存在: 404。
浏览器用户会被 meta refresh 立即带进 SPA, 体验不变; 搜索引擎读到的是完整摘要。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from html import escape

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.models.research import ResearchReport
from backend.app.services import research_service

router = APIRouter()

_settings = get_settings()


def _site_origin(request: Request) -> str:
    """优先用配置的站点地址, 否则从请求推断。"""
    configured = getattr(_settings, "public_base_url", "") or ""
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


def _clip(text: str, limit: int = 240) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _render_report_html(*, origin: str, report: ResearchReport) -> str:
    report_id = str(report.id)
    app_url = f"/app/reports/{report_id}"
    canonical = f"{origin}/reports/{report_id}"
    title = escape(str(report.title or "量化研究报告"))
    summary = escape(
        _clip(str(report.summary or report.hypothesis or ""))
        or "QuantLab AI 上的一份量化研究报告。"
    )
    symbol = escape(str(report.symbol or ""))
    grade = escape(str(report.grade or ""))
    created = report.created_at or datetime.now(timezone.utc)
    created_iso = created.isoformat()

    keywords = escape(f"量化研究,{report.symbol},因子研究,QuantLab AI".strip(","))

    jsonld = f"""{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{summary}",
  "datePublished": "{escape(created_iso)}",
  "about": "{symbol}",
  "isAccessibleForFree": true,
  "url": "{escape(canonical)}",
  "publisher": {{ "@type": "Organization", "name": "QuantLab AI" }}
}}"""

    body_meta = []
    if symbol:
        body_meta.append(f"<span>标的 {symbol}</span>")
    if grade:
        body_meta.append(f"<span>评级 {grade}</span>")
    meta_line = " · ".join(body_meta)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} · QuantLab AI</title>
  <meta name="description" content="{summary}" />
  <meta name="keywords" content="{keywords}" />
  <meta name="robots" content="index,follow" />
  <link rel="canonical" href="{escape(canonical)}" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{summary}" />
  <meta property="og:url" content="{escape(canonical)}" />
  <meta property="og:site_name" content="QuantLab AI" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{summary}" />
  <meta http-equiv="refresh" content="0;url={app_url}" />
  <script type="application/ld+json">{jsonld}</script>
</head>
<body>
  <main style="font-family:system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem;">
    <h1 style="font-size:1.35rem;">{title}</h1>
    <p style="color:#64748b;">{meta_line}</p>
    <p>{summary}</p>
    <p><a href="{app_url}">查看完整研究报告 →</a></p>
  </main>
</body>
</html>"""


@router.get("/reports/{report_id}", include_in_schema=False, response_class=HTMLResponse)
def report_seo_preview(
    report_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        report = research_service.get_report(db, uuid.UUID(report_id))
    except ValueError:
        return HTMLResponse("<html><body>报告不存在</body></html>", status_code=404)
    if report is None or not report.is_public:
        return HTMLResponse(
            "<html><body>报告不存在或未公开</body></html>", status_code=404
        )
    html = _render_report_html(origin=_site_origin(request), report=report)
    resp = HTMLResponse(html)
    resp.headers["Cache-Control"] = "public, max-age=300"
    return resp


@router.get("/sitemap.xml", include_in_schema=False, response_class=PlainTextResponse)
def sitemap(request: Request, db: Session = Depends(get_db)) -> PlainTextResponse:
    origin = _site_origin(request)
    static_paths = ["/app/", "/app/feed", "/app/leaderboards", "/app/pricing"]
    urls: list[str] = [f"  <url><loc>{escape(origin + p)}</loc></url>" for p in static_paths]
    for rid, updated in research_service.public_report_ids(db):
        lastmod = (updated or datetime.now(timezone.utc)).date().isoformat()
        loc = escape(f"{origin}/reports/{rid}")
        urls.append(
            f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>"
        )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    resp = PlainTextResponse(body, media_type="application/xml")
    resp.headers["Cache-Control"] = "public, max-age=600"
    return resp

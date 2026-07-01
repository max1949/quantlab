"""分享链接 HTML 预览 (OG 标签) — 微信/社群爬虫读标题摘要, 浏览器自动进 SPA。"""

from __future__ import annotations

from html import escape

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services import share_service

router = APIRouter()


def _render_share_html(*, token: str, title: str, summary: str, researcher: str) -> str:
    app_url = f"/app/share/{token}"
    safe_title = escape(title)
    safe_summary = escape(summary)
    safe_researcher = escape(researcher)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{safe_title} · QuantLab AI</title>
  <meta name="description" content="{safe_summary}" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{safe_title}" />
  <meta property="og:description" content="{safe_summary}" />
  <meta property="og:site_name" content="QuantLab AI" />
  <meta http-equiv="refresh" content="0;url={app_url}" />
  <link rel="canonical" href="/share/{escape(token)}" />
</head>
<body>
  <main style="font-family:system-ui,sans-serif;max-width:36rem;margin:2rem auto;padding:0 1rem;">
    <h1 style="font-size:1.25rem;">{safe_title}</h1>
    <p style="color:#64748b;">{safe_researcher}</p>
    <p>{safe_summary}</p>
    <p><a href="{app_url}">查看完整研究 →</a></p>
  </main>
</body>
</html>"""


@router.get("/share/{token}", include_in_schema=False, response_class=HTMLResponse)
def share_link_preview(
    token: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        share = share_service.get_share(db, token)
    except share_service.ShareNotFoundError:
        return HTMLResponse("<html><body>分享不存在或已失效</body></html>", status_code=404)

    card = share.card or {}
    title = str(card.get("title") or "量化研究报告")
    summary = str(card.get("summary") or card.get("hypothesis") or "")[:240]
    researcher = str(card.get("researcher") or "")
    return HTMLResponse(_render_share_html(token=token, title=title, summary=summary, researcher=researcher))

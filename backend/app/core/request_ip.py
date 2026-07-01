"""客户端 IP 提取 (支持反向代理 / Cloudflare Tunnel)。"""

from __future__ import annotations

from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    for header in (
        "cf-connecting-ip",
        "x-forwarded-for",
        "x-real-ip",
    ):
        raw = request.headers.get(header)
        if raw:
            return raw.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"

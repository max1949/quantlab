"""客户端 IP 提取 (支持反向代理 / Cloudflare Tunnel)。"""

from __future__ import annotations

import ipaddress

from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    direct = request.client.host if request.client else "unknown"
    if _trusted_proxy(direct):
        for header in (
            "cf-connecting-ip",
            "x-forwarded-for",
            "x-real-ip",
        ):
            raw = request.headers.get(header)
            if raw:
                return raw.split(",")[0].strip()
    if request.client:
        return direct
    return "unknown"


def _trusted_proxy(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return host in {"localhost", "testclient"}
    return ip.is_loopback or ip.is_private

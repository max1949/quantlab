"""Request locale from Accept-Language (default en)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import Depends, Request

Locale = Literal["en", "zh"]


def parse_locale(accept_language: str | None) -> Locale:
    if not accept_language:
        return "en"
    low = accept_language.lower()
    if low.startswith("zh") or "zh-" in low:
        return "zh"
    return "en"


def get_request_locale(request: Request) -> Locale:
    return parse_locale(request.headers.get("accept-language"))


RequestLocale = Annotated[Locale, Depends(get_request_locale)]

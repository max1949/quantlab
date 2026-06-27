"""外部 LLM 客户端 (Sprint 7) —— 唯一发起网络调用的地方。

OpenAI 兼容的 /chat/completions 接口 (DeepSeek / OpenAI / Moonshot 等均可,
通过 .env 的 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL 切换)。

未配置 api_key 时 `is_enabled()` 返回 False, 上层 (ai_service) 改用 engine 本地规则分析。
"""

from __future__ import annotations

import httpx

from backend.app.core.config import get_settings


class LLMError(Exception):
    """LLM 调用失败 (网络/鉴权/响应异常)。"""


def is_enabled() -> bool:
    s = get_settings()
    return bool(s.ai_enabled and s.llm_api_key)


def model_name() -> str:
    return get_settings().llm_model


def complete(system: str, user: str) -> str:
    """调用 chat completion, 返回助手文本。失败抛 LLMError。"""
    s = get_settings()
    if not s.llm_api_key:
        raise LLMError("未配置 LLM_API_KEY")

    url = s.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {s.llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": s.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": s.llm_temperature,
        "stream": False,
    }
    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=s.llm_timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise LLMError(str(exc)) from exc

"""Redis 滑动窗口限流 (防刷注册/登录/兑换)。"""

from __future__ import annotations

import redis

from backend.app.core.config import get_settings

SIGNUP_LIMITS = (5, 3600), (20, 86_400)  # hourly, daily per IP
LOGIN_LIMITS = (30, 3600)
CAPTCHA_LIMITS = (60, 3600)
REDEEM_LIMITS = (12, 3600), (30, 86_400)  # hourly/daily per user + 24/h IP


class RateLimitExceeded(Exception):
    """请求过于频繁。"""


def _redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def consume(bucket: str, max_calls: int, window_seconds: int) -> bool:
    """返回 True 表示允许; False 表示超限。"""
    try:
        r = _redis()
        key = f"ql:rl:{bucket}"
        count = r.incr(key)
        if count == 1:
            r.expire(key, window_seconds)
        return count <= max_calls
    except redis.RedisError:
        return True


def require_rate_limit(bucket: str, max_calls: int, window_seconds: int) -> None:
    if get_settings().rate_limit_disabled:
        return
    if not consume(bucket, max_calls, window_seconds):
        raise RateLimitExceeded("请求过于频繁，请稍后再试")


def check_signup(ip: str) -> None:
    require_rate_limit(f"signup:ip:{ip}", SIGNUP_LIMITS[0][0], SIGNUP_LIMITS[0][1])
    require_rate_limit(f"signup:ip:{ip}:day", SIGNUP_LIMITS[1][0], SIGNUP_LIMITS[1][1])


def check_login(ip: str) -> None:
    require_rate_limit(f"login:ip:{ip}", LOGIN_LIMITS[0], LOGIN_LIMITS[1])


def check_captcha(ip: str) -> None:
    require_rate_limit(f"captcha:ip:{ip}", CAPTCHA_LIMITS[0], CAPTCHA_LIMITS[1])


def check_redeem(ip: str, user_id: str) -> None:
    require_rate_limit(f"redeem:ip:{ip}", 24, 3600)
    require_rate_limit(f"redeem:user:{user_id}", REDEEM_LIMITS[0][0], REDEEM_LIMITS[0][1])
    require_rate_limit(
        f"redeem:user:{user_id}:day", REDEEM_LIMITS[1][0], REDEEM_LIMITS[1][1]
    )

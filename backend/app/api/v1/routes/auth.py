"""认证路由: 注册 / 登录 / 验证码。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.auth.security import create_access_token
from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.core.request_ip import get_client_ip
from backend.app.schemas.user import RegisterOut, Token, UserCreate, UserLogin, UserOut
from backend.app.services import (
    captcha_service,
    growth_service,
    referral_service,
    rate_limit,
    sso_service,
    user_service,
)

router = APIRouter()


def _verify_captcha(token: str | None, answer: str | None) -> None:
    if get_settings().captcha_disabled:
        return
    if not captcha_service.verify_captcha(answer or "", token or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期",
        )


@router.get("/captcha", summary="获取图形验证码")
def get_captcha(request: Request) -> dict:
    try:
        rate_limit.check_captcha(get_client_ip(request))
    except rate_limit.RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    issued = captcha_service.issue_captcha()
    if not issued:
        raise HTTPException(status_code=503, detail="验证码服务不可用")
    return {"token": issued["token"], "svg": issued["svg"]}


@router.post(
    "/register",
    response_model=RegisterOut,
    status_code=status.HTTP_201_CREATED,
    summary="注册新用户 (默认等级 L0 观察员; 可带 user_type 分流与 ref 邀请码)",
)
def register(
    payload: UserCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> RegisterOut:
    try:
        rate_limit.check_signup(get_client_ip(request))
    except rate_limit.RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    _verify_captcha(payload.captcha_token, payload.captcha_answer)
    try:
        user = user_service.create_user(db, payload)
    except user_service.UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{exc.field} 已被注册",
        )
    if payload.ref:
        referral_service.link_referral(db, user, payload.ref)
    growth_service.log_event(db, "register", user.id, {"user_type": user.user_type})
    db.refresh(user)
    token = create_access_token(subject=str(user.id))
    return RegisterOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token, summary="登录获取 JWT")
def login(
    payload: UserLogin,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    try:
        rate_limit.check_login(get_client_ip(request))
    except rate_limit.RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    _verify_captcha(payload.captcha_token, payload.captcha_answer)
    try:
        user = user_service.authenticate(db, payload.identifier, payload.password)
    except user_service.InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码错误",
        )
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


def _sso_redirect_uri(request: Request) -> str:
    settings = get_settings()
    origin = (settings.public_base_url or str(request.base_url)).rstrip("/")
    return f"{origin}/api/v1/auth/sso/callback"


@router.get("/sso/config", summary="SSO 是否启用")
def sso_config() -> dict:
    return {"enabled": sso_service.sso_configured()}


@router.get("/sso/login", summary="发起企业 SSO 登录 (重定向到 IdP)")
def sso_login(request: Request) -> RedirectResponse:
    if not sso_service.sso_configured():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SSO 未启用")
    url = sso_service.build_authorize_url(_sso_redirect_uri(request))
    return RedirectResponse(url=url)


@router.get("/sso/callback", summary="企业 SSO 回调 (交换令牌并签发本站 JWT)")
def sso_callback(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    settings = get_settings()
    origin = (settings.public_base_url or str(request.base_url)).rstrip("/")
    if not sso_service.sso_configured():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SSO 未启用")
    if error or not code or not state:
        return RedirectResponse(url=f"{origin}/app/login?sso_error=1")
    if not sso_service.verify_state(state):
        return RedirectResponse(url=f"{origin}/app/login?sso_error=state")
    try:
        tokens = sso_service.exchange_code(code, _sso_redirect_uri(request))
        userinfo = sso_service.fetch_userinfo(tokens.get("access_token", ""))
        user = sso_service.get_or_create_user(db, userinfo)
    except sso_service.SsoError:
        return RedirectResponse(url=f"{origin}/app/login?sso_error=exchange")
    growth_service.log_event(db, "sso_login", user.id, {})
    token = create_access_token(subject=str(user.id))
    return RedirectResponse(url=f"{origin}/app/login?sso_token={token}")

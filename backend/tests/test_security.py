"""认证原语与等级闸门的单元测试 (不依赖 DB/HTTP)。"""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest
from fastapi import HTTPException

from backend.app.auth.deps import require_level
from backend.app.auth.security import (
    ACCESS_TOKEN_TYPE,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.models.user import User, UserLevel


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    token = create_access_token(subject="user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == ACCESS_TOKEN_TYPE


def test_expired_token_rejected():
    token = create_access_token(subject="u", expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


def test_require_level_allows_and_blocks():
    gate = require_level(UserLevel.L2)
    l2_user = User(username="r", email="r@x.io", hashed_password="x", level=2)
    l1_user = User(username="a", email="a@x.io", hashed_password="x", level=1)

    assert gate(l2_user) is l2_user  # 满足: 等级足够
    with pytest.raises(HTTPException) as exc:
        gate(l1_user)
    assert exc.value.status_code == 403


def test_user_level_label():
    assert UserLevel.L0.label == "观察员"
    assert UserLevel.L3.label == "进阶研究员"

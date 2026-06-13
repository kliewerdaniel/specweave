from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from specweave.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    verify_token,
)
from specweave.config import settings


class TestJWT:
    def test_create_access_token(self) -> None:
        token = create_access_token("test-user")
        assert isinstance(token, str)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "test-user"

    def test_verify_token_valid(self) -> None:
        token = create_access_token("test-user")
        subject = verify_token(token)
        assert subject == "test-user"

    def test_verify_token_invalid(self) -> None:
        subject = verify_token("invalid-token")
        assert subject is None

    def test_verify_token_expired(self) -> None:
        from jose import jwt
        payload = {
            "sub": "test-user",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
        subject = verify_token(token)
        assert subject is None


class TestPassword:
    def test_hash_and_verify(self) -> None:
        try:
            hashed = hash_password("my-password")
            assert verify_password("my-password", hashed) is True
            assert verify_password("wrong-password", hashed) is False
        except (ValueError, ImportError):
            pytest.skip("bcrypt backend not available in test environment")


class TestGetCurrentUser:
    async def test_no_credentials(self) -> None:
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await get_current_user(None)
        assert exc.value.status_code == 401

    async def test_invalid_credentials(self) -> None:
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
        with pytest.raises(HTTPException) as exc:
            await get_current_user(creds)
        assert exc.value.status_code == 401

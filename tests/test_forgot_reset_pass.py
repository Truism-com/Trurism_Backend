"""
Tests for forgot-password / reset-password flow.
Mocks aiosmtplib and Redis so no real services are needed.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_database_session
from app.auth.models import User
from app.auth.services import AuthService
from app.core.security import SecurityManager


# ── helpers ──────────────────────────────────────────────────────────────────

def make_user(email="test@example.com") -> User:
    return User(
        id=1,
        email=email,
        password_hash="$2b$12$fakehashfortesting",  # no real bcrypt needed
        name="Test User",
        is_active=True,
        is_verified=True,
    )


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """Minimal async DB session stub."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """In-memory dict acting as Redis."""
    store = {}

    redis = MagicMock()
    redis.setex = AsyncMock(side_effect=lambda k, ttl, v: store.update({k: v}))
    redis.get = AsyncMock(side_effect=lambda k: store.get(k))
    redis.incr = AsyncMock(side_effect=lambda k: store.update({k: int(store.get(k, 0)) + 1}) or store[k])
    redis.expire = AsyncMock(return_value=True)
    redis.delete = AsyncMock(side_effect=lambda k: store.pop(k, None))
    return redis, store


# ── tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_forgot_password_sends_otp(mock_db, mock_redis):
    """Happy path: valid email → OTP stored and email sent."""
    redis_client, store = mock_redis
    user = make_user()

    with (
        patch("app.auth.services.get_redis_client", return_value=redis_client),
        patch("app.auth.api.email_service.send_otp", new_callable=AsyncMock) as mock_send,
        patch("app.auth.services.AuthService.get_user_by_email", new_callable=AsyncMock, return_value=user),
        patch("app.core.database.get_database_session", return_value=mock_db),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/auth/forgot-password",
                json={"email": user.email},
            )

    assert resp.status_code == 200
    mock_send.assert_awaited_once()
    # OTP was stored under the expected key
    assert f"pwd_reset_otp:{user.email}" in store


@pytest.mark.asyncio
async def test_reset_password_success(mock_db, mock_redis):
    """Valid OTP → password is changed and OTP key is deleted."""
    redis_client, store = mock_redis
    user = make_user()
    store[f"pwd_reset_otp:{user.email}"] = "123456"

    with (
        patch("app.auth.services.get_redis_client", return_value=redis_client),
        patch("app.auth.services.AuthService.get_user_by_email", new_callable=AsyncMock, return_value=user),
        patch("app.core.database.get_database_session", return_value=mock_db),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/auth/reset-password",
                json={
                    "email": user.email,
                    "otp": "123456",
                    "new_password": "NewPassw0rd!",
                },
            )

    assert resp.status_code == 200
    # OTP consumed
    assert f"pwd_reset_otp:{user.email}" not in store
    # Password actually changed
    assert SecurityManager.verify_password("NewPassw0rd!", user.password_hash)


@pytest.mark.asyncio
async def test_reset_password_expired_otp(mock_db, mock_redis):
    """Expired/missing OTP → HTTP 400."""
    redis_client, store = mock_redis
    # No OTP in store = simulates expiry

    app.dependency_overrides[get_database_session] = lambda: mock_db

    with patch("app.auth.services.get_redis_client", return_value=redis_client):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/auth/reset-password",
                json={
                    "email": "test@example.com",
                    "otp": "999999",
                    "new_password": "NewPassw0rd!",
                },
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_wrong_otp(mock_db, mock_redis):
    """Wrong OTP → HTTP 400."""
    redis_client, store = mock_redis
    store["pwd_reset_otp:test@example.com"] = "123456"

    app.dependency_overrides[get_database_session] = lambda: mock_db

    with patch("app.auth.services.get_redis_client", return_value=redis_client):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/auth/reset-password",
                json={
                    "email": "test@example.com",
                    "otp": "000000",
                    "new_password": "NewPassw0rd!",
                },
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_otp_expired_does_not_increment_attempts(mock_db, mock_redis):
    redis_client, store = mock_redis
    service = AuthService(mock_db)

    with patch("app.auth.services.get_redis_client", return_value=redis_client):
        with pytest.raises(HTTPException) as exc_info:
            await service.verify_otp_and_reset_password(
                email="test@example.com",
                otp="999999",
                new_password="NewPassw0rd!",
            )

    assert exc_info.value.status_code == 400
    assert "otp_attempts:test@example.com" not in store
    redis_client.incr.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_otp_wrong_value_increments_attempts(mock_db, mock_redis):
    redis_client, store = mock_redis
    service = AuthService(mock_db)
    store["pwd_reset_otp:test@example.com"] = "123456"

    with patch("app.auth.services.get_redis_client", return_value=redis_client):
        with pytest.raises(HTTPException) as exc_info:
            await service.verify_otp_and_reset_password(
                email="test@example.com",
                otp="000000",
                new_password="NewPassw0rd!",
            )

    assert exc_info.value.status_code == 400
    assert store["otp_attempts:test@example.com"] == 1
    redis_client.expire.assert_awaited_once_with("otp_attempts:test@example.com", 900)

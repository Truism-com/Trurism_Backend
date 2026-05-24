import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_forgot_password_always_returns_200(client):
    resp = await client.post("/auth/forgot-password", json={
        "email": "doesnotexist@example.com"
    })

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_otp_expires_after_ttl():
    mock_redis = AsyncMock()

    with patch("app.auth.services.get_redis_client", return_value=mock_redis) as mock_getter:
        # Force reimport so the patched getter is used
        import app.auth.services as auth_mod
        original_getter = auth_mod.get_redis_client
        auth_mod.get_redis_client = lambda: mock_redis   # replace directly on module

        service = AuthService(db=AsyncMock())
        await service.generate_and_store_otp("test@example.com")

        auth_mod.get_redis_client = original_getter  # restore

    assert mock_redis.set.call_args is not None, "OTP stored WITHOUT expiry!"
    kwargs = mock_redis.set.call_args.kwargs
    assert "ex" in kwargs or "px" in kwargs, f"No TTL in Redis.set call: {mock_redis.set.call_args}"


@pytest.mark.asyncio
async def test_reset_password_invalid_otp_rejected(client):
    resp = await client.post("/auth/reset_password", json={
        "email": "test@example.com",
        "otp": "000000",
        "new_password": "NewSecure123!"
    })

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_otp_not_reusable():

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=b"123456")
    mock_redis.delete = AsyncMock()

    with patch("app.auth.services.get_redis_client", return_value=mock_redis):
        from app.auth.services import AuthService
        mock_db = AsyncMock()
        service = AuthService(db=mock_db)

        try:
            await service.verify_otp_and_reset_password(
                email="test@example.com", otp="123456", new_password="New123!"
            )
        except Exception:
            pass  


    mock_redis.delete.assert_called_once()
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
    from unittest.mock import AsyncMock
    from app.auth import services as auth_mod

    mock_redis = AsyncMock()
    original = auth_mod.get_redis_client
    auth_mod.get_redis_client = lambda: mock_redis  

    try:
        service = auth_mod.AuthService(db=AsyncMock())
        await service.generate_and_store_otp("test@example.com")
    finally:
        auth_mod.get_redis_client = original  

    assert mock_redis.set.call_args is not None, "Redis.set was never called"
    kwargs = mock_redis.set.call_args.kwargs
    assert "ex" in kwargs or "px" in kwargs, f"No TTL passed to Redis.set: {mock_redis.set.call_args}"


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_reset_password_invalid_otp_rejected(client):

    import app.auth.services as auth_mod
    from unittest.mock import AsyncMock

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=b"999999")  
    original = auth_mod.get_redis_client
    auth_mod.get_redis_client = lambda: mock_redis

    try:
        resp = await client.post("/auth/reset_password", json={
            "email": "test@example.com",
            "otp": "000000",             
            "new_password": "NewSecure123!"
        })
    finally:
        auth_mod.get_redis_client = original

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_otp_not_reusable():
    from unittest.mock import AsyncMock
    import app.auth.services as auth_mod

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=b"123456")
    mock_redis.delete = AsyncMock()

    original = auth_mod.get_redis_client
    auth_mod.get_redis_client = lambda: mock_redis

    try:
        service = auth_mod.AuthService(db=AsyncMock())
        try:
            await service.verify_otp_and_reset_password(
                email="test@example.com", otp="123456", new_password="New123!"
            )
        except Exception:
            pass  #
    finally:
        auth_mod.get_redis_client = original

    
    mock_redis.delete.assert_called_once()
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
    import app.auth.services as auth_mod

    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()

    mock_user = MagicMock()
    mock_user.email = "test@example.com"

    original = auth_mod.get_redis_client
    auth_mod.get_redis_client = lambda: mock_redis

    try:
        service = auth_mod.AuthService(db=AsyncMock())
        service.get_user_by_email = AsyncMock(return_value=mock_user)
        await service.generate_and_store_otp("test@example.com")
    finally:
        auth_mod.get_redis_client = original

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args.args
    assert call_args[1] == 900, f"OTP TTL should be 900 seconds, got {call_args[1]}"


@pytest.mark.asyncio
async def test_reset_password_invalid_otp_rejected():
    import app.auth.services as auth_mod

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=[b"0", b"999999"])
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock()

    original = auth_mod.get_redis_client
    auth_mod.get_redis_client = lambda: mock_redis

    try:
        service = auth_mod.AuthService(db=AsyncMock())
        with pytest.raises(Exception) as exc_info:
            await service.verify_otp_and_reset_password(
                email="test@example.com",
                otp="000000",        
                new_password="NewSecure123!"
            )
        assert exc_info.value.status_code == 400
    finally:
        auth_mod.get_redis_client = original


@pytest.mark.asyncio
async def test_reset_password_otp_not_reusable():
    import app.auth.services as auth_mod

    mock_redis = AsyncMock()

    mock_redis.get = AsyncMock(side_effect=[b"0", b"123456"])
    mock_redis.delete = AsyncMock()

    original = auth_mod.get_redis_client
    auth_mod.get_redis_client = lambda: mock_redis

    try:
        service = auth_mod.AuthService(db=AsyncMock())
        service.get_user_by_email = AsyncMock(return_value=MagicMock(id=1))
        try:
            await service.verify_otp_and_reset_password(
                email="test@example.com", otp="123456", new_password="New123!"
            )
        except Exception:
            pass  
    finally:
        auth_mod.get_redis_client = original


    deleted_keys = [call.args[0] for call in mock_redis.delete.call_args_list]
    assert any("pwd_reset_otp" in k for k in deleted_keys), \
        "OTP key never deleted — OTP is replayable!"
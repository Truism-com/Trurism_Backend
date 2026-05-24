import pytest

@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "Secure123!",
        "name": "New User",
        "role": "customer",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "password" not in body        
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "Secure123!", "name": "A"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)

    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_admin_role_rejected(client):
    """Schema validator must block self-registration as ADMIN."""
    resp = await client.post("/auth/register", json={
        "email": "hacker@example.com",
        "password": "Secure123!",
        "name": "Hacker",
        "role": "admin",        
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_wrong_password(client, auth_tokens):
    resp = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "WRONGPASSWORD",
    })

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "anything",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_returns_both_tokens(client, auth_tokens):
    assert "access_token" in auth_tokens
    assert "refresh_token" in auth_tokens
    assert "expires_in" in auth_tokens
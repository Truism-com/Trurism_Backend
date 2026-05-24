import pytest

@pytest.mark.asyncio
async def test_refresh_returns_new_access_token(client, auth_tokens):
    resp = await client.post("/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"]
    })

    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_logout_then_access_denied(client, auth_tokens):
    """After logout the old access token must be blacklisted."""
    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    logout = await client.post("/auth/logout", headers=headers)
    assert logout.status_code == 200


    me = await client.get("/auth/me", headers=headers)

    assert me.status_code == 401


@pytest.mark.asyncio
async def test_revoked_refresh_token_rejected(client, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    # Logout with refresh token → it gets revoked
    await client.post("/auth/logout", headers=headers,params={"refresh_token": auth_tokens["refresh_token"]})


    resp = await client.post("/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"]
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_tampered_access_token_rejected(client):
    fake = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI5OTk5OTkifQ.INVALIDSIG"
    resp = await client.get("/auth/me",
                            headers={"Authorization": f"Bearer {fake}"})
    assert resp.status_code == 401
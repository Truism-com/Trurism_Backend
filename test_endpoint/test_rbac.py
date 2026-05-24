import pytest

@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 403   # or 401

@pytest.mark.asyncio
async def test_customer_cannot_access_admin_endpoint(client, auth_header):
    resp = await client.get("/admin/analytics", headers=auth_header)

    assert resp.status_code in (403, 404)

@pytest.mark.asyncio
async def test_unapproved_agent_cannot_book(client):

    await client.post("/auth/register", json={
        "email": "agent@example.com", "password": "Secure123!",
        "name": "Agent", "role": "agent",
        "company_name": "Travel Co", "pan_number": "ABCDE1234F"
    })
    resp = await client.post("/auth/login", json={
        "email": "agent@example.com", "password": "Secure123!"
    })
    token = resp.json().get("access_token", "")
    headers = {"Authorization": f"Bearer {token}"}

    booking_resp = await client.post("/bookings/flights",headers=headers, json={})

    assert booking_resp.status_code == 403

@pytest.mark.asyncio
async def test_admin_only_superadmin_endpoint(client):
    pytest.skip("Implement once admin seeding fixture is available")
"""
Tests for authentication, credits, and admin features
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # 1. Register
    reg_resp = await client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "password123"},
    )
    assert reg_resp.status_code == 200
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "alice"
    assert data["user"]["credits"] == 5

    # 2. Duplicate registration should fail
    dup_resp = await client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "password123"},
    )
    assert dup_resp.status_code == 400

    # 3. Login
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["access_token"]

    # 4. Get Current User (/me)
    me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_admin_access_and_recharge(client: AsyncClient, db_session):
    # Register regular user
    user_resp = await client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "password123"},
    )
    bob_token = user_resp.json()["access_token"]
    bob_id = user_resp.json()["user"]["id"]

    # Regular user cannot access /admin/users
    forbidden_resp = await client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert forbidden_resp.status_code == 403

    # Promote bob to admin directly in db
    from models.user import User
    from sqlalchemy import select
    res = await db_session.execute(select(User).where(User.id == bob_id))
    bob = res.scalar_one()
    bob.is_admin = True
    await db_session.commit()

    # Now bob can access admin routes
    admin_users_resp = await client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert admin_users_resp.status_code == 200
    users = admin_users_resp.json()
    assert len(users) >= 1

    # Recharge credits
    recharge_resp = await client.post(
        f"/api/admin/users/{bob_id}/credits",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={"amount": 20, "reason": "Monthly reward"},
    )
    assert recharge_resp.status_code == 200

    # Check /me/credits
    credits_resp = await client.get(
        "/api/auth/me/credits",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert credits_resp.status_code == 200
    log_data = credits_resp.json()
    assert log_data["credits"] == 25  # 5 initial + 20 added
    assert len(log_data["logs"]) >= 1

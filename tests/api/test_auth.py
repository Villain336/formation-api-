"""Tests for authentication endpoints."""

import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "securepassword123",
        "full_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "New User"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    # Register first
    await client.post("/api/v1/auth/register", json={
        "email": "dupe@example.com",
        "password": "password123",
        "full_name": "First User",
    })
    # Try duplicate
    response = await client.post("/api/v1/auth/register", json={
        "email": "dupe@example.com",
        "password": "password456",
        "full_name": "Second User",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    # Register
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "mypassword",
        "full_name": "Login User",
    })
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "mypassword",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "password": "correctpassword",
        "full_name": "User",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, auth_token):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

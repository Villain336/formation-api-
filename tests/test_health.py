"""Basic health check tests."""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Formation API"


@pytest.mark.asyncio
async def test_openapi(client):
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Formation API"
    assert "/api/v1/auth/register" in data["paths"]
    assert "/api/v1/orders" in data["paths"]


@pytest.mark.asyncio
async def test_api_docs(client):
    response = await client.get("/api/docs")
    assert response.status_code == 200

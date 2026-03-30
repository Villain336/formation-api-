"""Tests for state requirements endpoints."""

import pytest

from app.models.entity import EntityType, StateRequirement


@pytest.mark.asyncio
async def test_list_entity_types(client, db_session):
    et = EntityType(name="llc", display_name="LLC", description="Limited Liability Company")
    db_session.add(et)
    await db_session.commit()

    response = await client.get("/api/v1/states/entity-types")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "llc"


@pytest.mark.asyncio
async def test_list_requirements(client, db_session):
    req = StateRequirement(
        state_code="FL",
        state_name="Florida",
        entity_type="llc",
        state_filing_fee=12500,
        standard_processing_days=5,
        filing_agency="FL DOS",
    )
    db_session.add(req)
    await db_session.commit()

    response = await client.get("/api/v1/states/requirements", params={"entity_type": "llc"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_state_requirement(client, db_session):
    req = StateRequirement(
        state_code="TX",
        state_name="Texas",
        entity_type="llc",
        state_filing_fee=30000,
        standard_processing_days=5,
        filing_agency="TX SOS",
    )
    db_session.add(req)
    await db_session.commit()

    response = await client.get("/api/v1/states/requirements/TX/llc")
    assert response.status_code == 200
    data = response.json()
    assert data["state_code"] == "TX"
    assert data["state_filing_fee"] == 30000


@pytest.mark.asyncio
async def test_get_nonexistent_state(client):
    response = await client.get("/api/v1/states/requirements/XX/llc")
    assert response.status_code == 404

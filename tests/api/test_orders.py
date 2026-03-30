"""Tests for order endpoints."""

import pytest

from app.models.entity import StateRequirement


@pytest.mark.asyncio
async def test_create_order(client, auth_token, db_session):
    # Seed state requirement first
    req = StateRequirement(
        state_code="DE",
        state_name="Delaware",
        entity_type="llc",
        state_filing_fee=9000,
        standard_processing_days=3,
        filing_agency="Delaware Division of Corporations",
        online_filing_available=True,
    )
    db_session.add(req)
    await db_session.commit()

    response = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "entity_type": "llc",
            "state_of_formation": "DE",
            "business_name": "Test Company LLC",
            "business_address_line1": "123 Main St",
            "business_city": "Wilmington",
            "business_state": "DE",
            "business_zip": "19801",
            "include_registered_agent": True,
            "include_ein": False,
            "members": [
                {
                    "role": "owner",
                    "full_name": "John Doe",
                    "ownership_percentage": 100,
                    "address_line1": "123 Main St",
                    "city": "Wilmington",
                    "state": "DE",
                    "zip_code": "19801",
                }
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["business_name"] == "Test Company LLC"
    assert data["state_of_formation"] == "DE"
    assert data["status"] == "draft"
    assert data["total_amount"] > 0
    assert data["order_number"].startswith("FORM-")
    assert len(data["members"]) == 1


@pytest.mark.asyncio
async def test_list_orders(client, auth_token):
    response = await client.get(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_name_check(client, db_session):
    req = StateRequirement(
        state_code="NY",
        state_name="New York",
        entity_type="llc",
        state_filing_fee=20000,
        standard_processing_days=7,
        filing_agency="NY DOS",
        naming_rules={
            "required_suffix": ["LLC", "L.L.C."],
            "restricted_words": ["bank", "insurance"],
        },
    )
    db_session.add(req)
    await db_session.commit()

    # Valid name
    response = await client.post("/api/v1/orders/name-check", json={
        "business_name": "My Cool Business LLC",
        "state": "NY",
        "entity_type": "llc",
    })
    assert response.status_code == 200
    assert response.json()["available"] is True

    # Missing suffix
    response = await client.post("/api/v1/orders/name-check", json={
        "business_name": "My Cool Business",
        "state": "NY",
        "entity_type": "llc",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False
    assert len(data["suggestions"]) > 0

    # Restricted word
    response = await client.post("/api/v1/orders/name-check", json={
        "business_name": "My Bank LLC",
        "state": "NY",
        "entity_type": "llc",
    })
    assert response.status_code == 200
    assert response.json()["available"] is False


@pytest.mark.asyncio
async def test_pricing(client, db_session):
    req = StateRequirement(
        state_code="WY",
        state_name="Wyoming",
        entity_type="llc",
        state_filing_fee=10000,
        expedited_fee=10000,
        standard_processing_days=3,
        expedited_processing_days=1,
        filing_agency="WY SOS",
    )
    db_session.add(req)
    await db_session.commit()

    response = await client.post(
        "/api/v1/orders/pricing",
        params={
            "entity_type": "llc",
            "state": "WY",
            "processing_speed": "standard",
            "include_registered_agent": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state_fee"] == 10000
    assert data["total_amount"] > 0
    assert "breakdown" in data

"""E2E tests: Test actual API functionality against a live server.

These tests hit real API endpoints to verify the complete request/response cycle
including auth, order creation, pricing, state data, and API key management.
"""

import re
import pytest
import httpx


class TestHealthAndSEO:
    """Test system endpoints and SEO artifacts."""

    def test_health_endpoint(self, base_url: str):
        resp = httpx.get(f"{base_url}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_api_health(self, base_url: str):
        resp = httpx.get(f"{base_url}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Formation API"

    def test_openapi_spec(self, base_url: str):
        resp = httpx.get(f"{base_url}/api/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        assert spec["info"]["title"] == "Formation API"
        assert "/api/v1/auth/register" in spec["paths"]
        assert "/api/v1/orders" in spec["paths"]

    def test_robots_txt(self, base_url: str):
        resp = httpx.get(f"{base_url}/robots.txt")
        assert resp.status_code == 200
        text = resp.text
        assert "User-agent: *" in text
        assert "Disallow: /api/" in text
        assert "Disallow: /dashboard/" in text
        assert "Sitemap:" in text

    def test_sitemap_xml(self, base_url: str):
        resp = httpx.get(f"{base_url}/sitemap.xml")
        assert resp.status_code == 200
        assert "urlset" in resp.text
        assert "/features" in resp.text
        assert "/pricing" in resp.text
        assert "/docs/quickstart" in resp.text
        assert "/legal/terms" in resp.text

    def test_security_headers(self, base_url: str):
        resp = httpx.get(f"{base_url}/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Content-Security-Policy" in resp.headers
        assert "Referrer-Policy" in resp.headers


class TestAuthFlow:
    """Test the complete authentication flow: register → login → get profile → API keys."""

    def test_register_new_user(self, api_url: str):
        resp = httpx.post(f"{api_url}/auth/register", json={
            "email": "e2e_user@example.com",
            "password": "securePass123!",
            "full_name": "E2E Test User",
            "company_name": "E2E Corp",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "e2e_user@example.com"
        assert data["user"]["full_name"] == "E2E Test User"
        assert data["user"]["plan"] == "free"

    def test_register_duplicate_fails(self, api_url: str):
        # Register first
        httpx.post(f"{api_url}/auth/register", json={
            "email": "dupe_e2e@example.com",
            "password": "pass123",
            "full_name": "Dupe",
        })
        # Try again
        resp = httpx.post(f"{api_url}/auth/register", json={
            "email": "dupe_e2e@example.com",
            "password": "pass456",
            "full_name": "Dupe 2",
        })
        assert resp.status_code == 400

    def test_login(self, api_url: str):
        # Register
        httpx.post(f"{api_url}/auth/register", json={
            "email": "login_e2e@example.com",
            "password": "mypassword",
            "full_name": "Login Test",
        })
        # Login
        resp = httpx.post(f"{api_url}/auth/login", json={
            "email": "login_e2e@example.com",
            "password": "mypassword",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, api_url: str):
        httpx.post(f"{api_url}/auth/register", json={
            "email": "wrongpw_e2e@example.com",
            "password": "correctpassword",
            "full_name": "User",
        })
        resp = httpx.post(f"{api_url}/auth/login", json={
            "email": "wrongpw_e2e@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_get_profile(self, api_url: str):
        # Register to get token
        reg = httpx.post(f"{api_url}/auth/register", json={
            "email": "profile_e2e@example.com",
            "password": "pass123",
            "full_name": "Profile User",
        })
        token = reg.json()["access_token"]

        resp = httpx.get(f"{api_url}/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200
        assert resp.json()["email"] == "profile_e2e@example.com"

    def test_unauthorized_access(self, api_url: str):
        resp = httpx.get(f"{api_url}/auth/me")
        assert resp.status_code == 401

    def test_invalid_token(self, api_url: str):
        resp = httpx.get(f"{api_url}/auth/me", headers={
            "Authorization": "Bearer invalid_token_here",
        })
        assert resp.status_code == 401

    def test_update_profile(self, api_url: str):
        reg = httpx.post(f"{api_url}/auth/register", json={
            "email": "update_e2e@example.com",
            "password": "pass123",
            "full_name": "Before",
        })
        token = reg.json()["access_token"]

        resp = httpx.patch(f"{api_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "After Update", "phone": "555-1234"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "After Update"
        assert resp.json()["phone"] == "555-1234"


class TestAPIKeyManagement:
    """Test the complete API key lifecycle."""

    def _get_auth(self, api_url: str, email: str) -> str:
        resp = httpx.post(f"{api_url}/auth/register", json={
            "email": email,
            "password": "pass123",
            "full_name": "Key Tester",
        })
        return resp.json()["access_token"]

    def test_create_api_key(self, api_url: str):
        token = self._get_auth(api_url, "keytest1@example.com")
        resp = httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Key",
                "environment": "test",
                "scopes": ["orders:read", "states:read"],
                "rate_limit_per_minute": 30,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Key"
        assert data["key"] is not None  # Key shown on creation
        assert data["key"].startswith("form_test_")
        assert data["environment"] == "test"
        assert "orders:read" in data["scopes"]
        assert data["rate_limit_per_minute"] == 30
        assert data["is_active"] is True

    def test_create_live_key(self, api_url: str):
        token = self._get_auth(api_url, "keytest2@example.com")
        resp = httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Live Key", "environment": "live"},
        )
        assert resp.status_code == 201
        assert resp.json()["key"].startswith("form_live_")

    def test_create_key_with_expiry(self, api_url: str):
        token = self._get_auth(api_url, "keytest3@example.com")
        resp = httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Expiring Key", "environment": "test", "expires_in_days": 30},
        )
        assert resp.status_code == 201
        assert resp.json()["expires_at"] is not None

    def test_list_api_keys(self, api_url: str):
        token = self._get_auth(api_url, "keytest4@example.com")
        # Create two keys
        httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Key 1", "environment": "test"},
        )
        httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Key 2", "environment": "live"},
        )

        resp = httpx.get(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        keys = resp.json()
        assert len(keys) == 2
        # Keys should NOT contain the full key value
        for k in keys:
            assert k["key"] is None

    def test_update_api_key(self, api_url: str):
        token = self._get_auth(api_url, "keytest5@example.com")
        create = httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Original", "environment": "test", "scopes": ["orders:read"]},
        )
        key_id = create.json()["id"]

        resp = httpx.patch(f"{api_url}/auth/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Name", "scopes": ["orders:read", "orders:write"]},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert "orders:write" in resp.json()["scopes"]

    def test_renew_api_key(self, api_url: str):
        token = self._get_auth(api_url, "keytest6@example.com")
        create = httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Renew Me", "environment": "test", "expires_in_days": 30},
        )
        key_id = create.json()["id"]

        resp = httpx.post(f"{api_url}/auth/api-keys/{key_id}/renew",
            headers={"Authorization": f"Bearer {token}"},
            json={"expires_in_days": 365},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True
        assert resp.json()["expires_at"] is not None

    def test_roll_api_key(self, api_url: str):
        token = self._get_auth(api_url, "keytest7@example.com")
        create = httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Roll Me", "environment": "test", "scopes": ["orders:read"]},
        )
        old_id = create.json()["id"]
        old_prefix = create.json()["key_prefix"]

        resp = httpx.post(f"{api_url}/auth/api-keys/{old_id}/roll",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"] is not None  # New key returned
        assert data["id"] != old_id  # New key ID
        assert data["name"] == "Roll Me"  # Same name
        assert "orders:read" in data["scopes"]  # Same scopes

    def test_delete_api_key(self, api_url: str):
        token = self._get_auth(api_url, "keytest8@example.com")
        create = httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Delete Me", "environment": "test"},
        )
        key_id = create.json()["id"]

        resp = httpx.delete(f"{api_url}/auth/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        # Verify it's deactivated
        keys = httpx.get(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        deactivated = [k for k in keys if k["id"] == key_id]
        assert len(deactivated) == 1
        assert deactivated[0]["is_active"] is False

    def test_invalid_scope_rejected(self, api_url: str):
        token = self._get_auth(api_url, "keytest9@example.com")
        resp = httpx.post(f"{api_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Bad Scope", "environment": "test", "scopes": ["invalid:scope"]},
        )
        assert resp.status_code == 400

    def test_list_scopes(self, api_url: str):
        resp = httpx.get(f"{api_url}/auth/scopes")
        assert resp.status_code == 200
        scopes = resp.json()["scopes"]
        assert "orders:read" in scopes
        assert "orders:write" in scopes
        assert "states:read" in scopes


class TestFormationOrders:
    """Test the formation order workflow."""

    def _auth(self, api_url: str, email: str) -> str:
        resp = httpx.post(f"{api_url}/auth/register", json={
            "email": email, "password": "pass123", "full_name": "Order Tester",
        })
        return resp.json()["access_token"]

    def test_create_order(self, api_url: str):
        token = self._auth(api_url, "order1@example.com")
        resp = httpx.post(f"{api_url}/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "entity_type": "llc",
                "state_of_formation": "DE",
                "business_name": "E2E Test Company LLC",
                "business_address_line1": "123 Test St",
                "business_city": "Wilmington",
                "business_state": "DE",
                "business_zip": "19801",
                "include_registered_agent": True,
                "include_ein": False,
                "members": [{
                    "role": "owner",
                    "full_name": "Test Owner",
                    "ownership_percentage": 100,
                    "address_line1": "123 Test St",
                    "city": "Wilmington",
                    "state": "DE",
                    "zip_code": "19801",
                }],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["entity_type"] == "llc"
        assert data["state_of_formation"] == "DE"
        assert data["business_name"] == "E2E Test Company LLC"
        assert data["order_number"].startswith("FORM-")
        assert data["total_amount"] > 0
        assert data["state_fee"] > 0
        assert data["service_fee"] > 0
        assert len(data["members"]) == 1

    def test_create_order_invalid_state(self, api_url: str):
        token = self._auth(api_url, "order2@example.com")
        resp = httpx.post(f"{api_url}/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "entity_type": "llc",
                "state_of_formation": "XX",
                "business_name": "Bad State LLC",
                "business_address_line1": "123 St",
                "business_city": "City",
                "business_state": "XX",
                "business_zip": "00000",
            },
        )
        assert resp.status_code == 400

    def test_list_orders(self, api_url: str):
        token = self._auth(api_url, "order3@example.com")
        # Create one order
        httpx.post(f"{api_url}/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "entity_type": "llc", "state_of_formation": "WY",
                "business_name": "WY Test LLC",
                "business_address_line1": "1 St", "business_city": "Cheyenne",
                "business_state": "WY", "business_zip": "82001",
            },
        )

        resp = httpx.get(f"{api_url}/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["orders"]) >= 1
        assert "page" in data

    def test_get_order(self, api_url: str):
        token = self._auth(api_url, "order4@example.com")
        create = httpx.post(f"{api_url}/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "entity_type": "llc", "state_of_formation": "DE",
                "business_name": "Get Test LLC",
                "business_address_line1": "1 St", "business_city": "Wilmington",
                "business_state": "DE", "business_zip": "19801",
            },
        )
        order_id = create.json()["id"]

        resp = httpx.get(f"{api_url}/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    def test_update_draft_order(self, api_url: str):
        token = self._auth(api_url, "order5@example.com")
        create = httpx.post(f"{api_url}/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "entity_type": "llc", "state_of_formation": "DE",
                "business_name": "Update Me LLC",
                "business_address_line1": "1 St", "business_city": "Wilmington",
                "business_state": "DE", "business_zip": "19801",
            },
        )
        order_id = create.json()["id"]

        resp = httpx.patch(f"{api_url}/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"business_name": "Updated Name LLC"},
        )
        assert resp.status_code == 200
        assert resp.json()["business_name"] == "Updated Name LLC"

    def test_add_member_to_order(self, api_url: str):
        token = self._auth(api_url, "order6@example.com")
        create = httpx.post(f"{api_url}/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "entity_type": "llc", "state_of_formation": "DE",
                "business_name": "Member Test LLC",
                "business_address_line1": "1 St", "business_city": "Wilmington",
                "business_state": "DE", "business_zip": "19801",
            },
        )
        order_id = create.json()["id"]

        resp = httpx.post(f"{api_url}/orders/{order_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "role": "manager",
                "full_name": "Jane Manager",
                "email": "jane@test.com",
                "ownership_percentage": 50,
                "address_line1": "456 Oak",
                "city": "Dover",
                "state": "DE",
                "zip_code": "19901",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["full_name"] == "Jane Manager"
        assert resp.json()["role"] == "manager"

    def test_order_not_found(self, api_url: str):
        token = self._auth(api_url, "order7@example.com")
        resp = httpx.get(f"{api_url}/orders/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestNameCheck:
    def test_name_check_basic(self, api_url: str):
        resp = httpx.post(f"{api_url}/orders/name-check", json={
            "business_name": "My Test Company LLC",
            "state": "DE",
            "entity_type": "llc",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "available" in data
        assert data["business_name"] == "My Test Company LLC"
        assert data["state"] == "DE"


class TestPricing:
    def test_pricing_standard(self, api_url: str):
        resp = httpx.post(f"{api_url}/orders/pricing", params={
            "entity_type": "llc",
            "state": "DE",
            "processing_speed": "standard",
            "include_registered_agent": True,
            "include_ein": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["state_fee"] == 9000  # $90
        assert data["total_amount"] > 0
        assert "breakdown" in data
        assert data["currency"] == "usd"

    def test_pricing_with_ein(self, api_url: str):
        base = httpx.post(f"{api_url}/orders/pricing", params={
            "entity_type": "llc", "state": "DE",
            "processing_speed": "standard",
            "include_registered_agent": False, "include_ein": False,
        }).json()

        with_ein = httpx.post(f"{api_url}/orders/pricing", params={
            "entity_type": "llc", "state": "DE",
            "processing_speed": "standard",
            "include_registered_agent": False, "include_ein": True,
        }).json()

        assert with_ein["total_amount"] > base["total_amount"]


class TestStateData:
    def test_list_entity_types(self, api_url: str):
        resp = httpx.get(f"{api_url}/states/entity-types")
        assert resp.status_code == 200
        types = resp.json()
        assert len(types) >= 1
        names = [t["name"] for t in types]
        assert "llc" in names

    def test_list_states(self, api_url: str):
        resp = httpx.get(f"{api_url}/states/requirements", params={"entity_type": "llc"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_get_state_detail(self, api_url: str):
        resp = httpx.get(f"{api_url}/states/requirements/DE/llc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["state_code"] == "DE"
        assert data["state_name"] == "Delaware"
        assert data["entity_type"] == "llc"
        assert data["state_filing_fee"] == 9000

    def test_nonexistent_state(self, api_url: str):
        resp = httpx.get(f"{api_url}/states/requirements/ZZ/llc")
        assert resp.status_code == 404

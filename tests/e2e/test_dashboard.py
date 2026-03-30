"""E2E tests: Verify dashboard pages render correctly."""

import re
import pytest
from playwright.sync_api import Page, expect


class TestDashboardOverview:
    def test_dashboard_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        expect(page).to_have_title(re.compile(r"Dashboard"))
        expect(page.locator("h1")).to_contain_text("Dashboard")

    def test_dashboard_has_sidebar(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        sidebar = page.locator(".dash-sidebar")
        expect(sidebar).to_be_visible()
        expect(sidebar.locator("a[href='/dashboard/api-keys']")).to_be_visible()
        expect(sidebar.locator("a[href='/dashboard/orders']")).to_be_visible()
        expect(sidebar.locator("a[href='/dashboard/settings']")).to_be_visible()

    def test_dashboard_has_stats(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        stats = page.locator(".dash-stat")
        assert stats.count() == 4
        expect(page.locator("text=Total Orders")).to_be_visible()
        expect(page.locator("text=Active Keys")).to_be_visible()
        expect(page.locator("text=API Requests")).to_be_visible()

    def test_dashboard_has_quickstart(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        expect(page.locator("text=Quick Start")).to_be_visible()
        expect(page.locator("text=Create an API key")).to_be_visible()

    def test_dashboard_has_resources(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        expect(page.locator("text=Resources")).to_be_visible()
        expect(page.locator("text=Documentation")).to_be_visible()

    def test_dashboard_has_create_key_button(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        expect(page.locator("a[href='/dashboard/api-keys']").first).to_be_visible()


class TestDashboardAPIKeys:
    def test_api_keys_page_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        expect(page).to_have_title(re.compile(r"API Keys"))

    def test_api_keys_has_create_form(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        expect(page.locator("text=Create New API Key")).to_be_visible()
        expect(page.locator("input#key-name")).to_be_visible()
        expect(page.locator("select#key-env")).to_be_visible()
        expect(page.locator("select#key-expiry")).to_be_visible()

    def test_api_keys_has_environment_options(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        select = page.locator("select#key-env")
        expect(select.locator("option[value='test']")).to_be_attached()
        expect(select.locator("option[value='live']")).to_be_attached()

    def test_api_keys_has_scope_checkboxes(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        checkboxes = page.locator("input[name='scopes']")
        assert checkboxes.count() >= 8  # At least 8 scope checkboxes
        # orders:read and orders:write should be checked by default
        expect(page.locator("input[value='orders:read']")).to_be_checked()
        expect(page.locator("input[value='orders:write']")).to_be_checked()

    def test_api_keys_has_rate_limit_input(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        rate_input = page.locator("input#key-rate")
        expect(rate_input).to_be_visible()
        assert rate_input.input_value() == "60"

    def test_api_keys_has_security_warning(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        expect(page.locator("text=shown only once")).to_be_visible()

    def test_api_keys_has_keys_table(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        expect(page.locator("text=Your API Keys")).to_be_visible()
        table = page.locator("table")
        assert table.count() >= 1

    def test_api_keys_has_best_practices(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        expect(page.locator("text=Key Management Best Practices")).to_be_visible()
        expect(page.locator("text=Rotate keys every 90 days")).to_be_visible()
        expect(page.locator("text=environment variables")).to_be_visible()

    def test_api_keys_has_expiry_options(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard/api-keys")
        select = page.locator("select#key-expiry")
        expect(select.locator("option[value='90']")).to_be_attached()
        # 90 days should be selected by default
        assert select.input_value() == "90"


class TestDashboardNavigation:
    def test_nav_to_api_keys(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        page.locator(".dash-sidebar a[href='/dashboard/api-keys']").click()
        expect(page).to_have_url(re.compile(r"/dashboard/api-keys"))

    def test_nav_to_orders(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        page.locator(".dash-sidebar a[href='/dashboard/orders']").click()
        expect(page).to_have_url(re.compile(r"/dashboard/orders"))

    def test_nav_to_settings(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        page.locator(".dash-sidebar a[href='/dashboard/settings']").click()
        expect(page).to_have_url(re.compile(r"/dashboard/settings"))

    def test_docs_link_in_sidebar(self, page: Page, base_url: str):
        page.goto(f"{base_url}/dashboard")
        docs_link = page.locator(".dash-sidebar a[href='/docs']")
        expect(docs_link).to_be_visible()
        expect(docs_link).to_have_attribute("target", "_blank")

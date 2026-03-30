"""E2E tests: Verify documentation pages load with correct content and navigation."""

import re
import pytest
from playwright.sync_api import Page, expect


class TestDocsOverview:
    def test_docs_overview_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        expect(page).to_have_title(re.compile(r"Documentation"))
        expect(page.locator("h1")).to_contain_text("Documentation")

    def test_docs_has_sidebar(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        sidebar = page.locator(".docs-sidebar")
        expect(sidebar).to_be_visible()
        expect(sidebar.locator("a[href='/docs/quickstart']")).to_be_visible()
        expect(sidebar.locator("a[href='/docs/authentication']")).to_be_visible()
        expect(sidebar.locator("a[href='/docs/api-reference']")).to_be_visible()

    def test_docs_has_quick_links(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        expect(page.locator("text=Quickstart Guide")).to_be_visible()
        expect(page.locator("text=Authentication")).to_be_visible()
        expect(page.locator("text=API Reference")).to_be_visible()

    def test_docs_shows_base_url(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        expect(page.locator("text=api.formation.dev")).to_be_visible()

    def test_docs_entity_types_table(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        expect(page.locator("code:text('llc')").first).to_be_visible()
        expect(page.locator("code:text('corporation')").first).to_be_visible()

    def test_docs_rate_limits_table(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        expect(page.locator("text=Rate Limits")).to_be_visible()


class TestQuickstartDocs:
    def test_quickstart_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/quickstart")
        expect(page).to_have_title(re.compile(r"Quickstart"))
        expect(page.locator("h1")).to_contain_text("Quickstart")

    def test_quickstart_has_steps(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/quickstart")
        expect(page.locator("text=Step 1")).to_be_visible()
        expect(page.locator("text=Step 2")).to_be_visible()
        expect(page.locator("text=Step 3")).to_be_visible()

    def test_quickstart_has_code_examples(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/quickstart")
        code_blocks = page.locator(".code-block")
        assert code_blocks.count() >= 4  # Register, create key, create order, payment

    def test_quickstart_has_curl_examples(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/quickstart")
        pre_blocks = page.locator("pre")
        assert pre_blocks.count() >= 4
        # Verify actual API endpoints in code examples
        content = page.content()
        assert "/api/v1/auth/register" in content
        assert "/api/v1/orders" in content

    def test_quickstart_has_order_status_flow(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/quickstart")
        expect(page.locator("text=draft")).to_be_visible()
        expect(page.locator("text=pending_payment")).to_be_visible()

    def test_quickstart_has_next_steps(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/quickstart")
        expect(page.locator("text=Next Steps")).to_be_visible()
        expect(page.locator("a[href='/docs/authentication']").first).to_be_visible()


class TestAuthenticationDocs:
    def test_auth_docs_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/authentication")
        expect(page).to_have_title(re.compile(r"Authentication"))
        expect(page.locator("h1")).to_contain_text("Authentication")

    def test_auth_docs_has_methods(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/authentication")
        expect(page.locator("text=JWT Bearer Token")).to_be_visible()
        expect(page.locator("text=API Key")).to_be_visible()

    def test_auth_docs_has_scopes_table(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/authentication")
        expect(page.locator("text=API Key Scopes")).to_be_visible()
        expect(page.locator("code:text('orders:read')").first).to_be_visible()
        expect(page.locator("code:text('orders:write')").first).to_be_visible()

    def test_auth_docs_has_key_format(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/authentication")
        expect(page.locator("text=form_test_")).to_be_visible()
        expect(page.locator("text=form_live_")).to_be_visible()

    def test_auth_docs_has_rotation(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/authentication")
        expect(page.locator("text=Key Rotation")).to_be_visible()

    def test_auth_docs_has_security_practices(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/authentication")
        expect(page.locator("text=Security Best Practices")).to_be_visible()


class TestAPIReferenceDocs:
    def test_api_ref_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/api-reference")
        expect(page).to_have_title(re.compile(r"API Reference"))
        expect(page.locator("h1")).to_contain_text("API Reference")

    def test_api_ref_has_all_sections(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/api-reference")
        expect(page.locator("h2#auth")).to_be_visible()
        expect(page.locator("h2#orders")).to_be_visible()
        expect(page.locator("h2#states")).to_be_visible()
        expect(page.locator("h2#payments")).to_be_visible()
        expect(page.locator("h2#webhooks")).to_be_visible()
        expect(page.locator("h2#compliance")).to_be_visible()
        expect(page.locator("h2#admin")).to_be_visible()

    def test_api_ref_has_method_badges(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/api-reference")
        expect(page.locator(".method--get").first).to_be_visible()
        expect(page.locator(".method--post").first).to_be_visible()
        expect(page.locator(".method--patch").first).to_be_visible()
        expect(page.locator(".method--delete").first).to_be_visible()

    def test_api_ref_has_endpoint_paths(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/api-reference")
        content = page.content()
        assert "/auth/register" in content
        assert "/orders" in content
        assert "/payments/create-intent" in content
        assert "/webhooks/endpoints" in content

    def test_api_ref_has_create_order_schema(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/api-reference")
        expect(page.locator("text=Create Order Request Body")).to_be_visible()
        expect(page.locator("text=entity_type").first).to_be_visible()

    def test_api_ref_has_webhook_events(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/api-reference")
        expect(page.locator("text=Webhook Event Types")).to_be_visible()
        expect(page.locator("code:text('order.created')").first).to_be_visible()
        expect(page.locator("code:text('payment.succeeded')").first).to_be_visible()

    def test_api_ref_has_error_format(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/api-reference")
        expect(page.locator("text=Error Responses")).to_be_visible()


class TestSecurityDocs:
    def test_security_docs_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/security")
        expect(page.locator("h1")).to_contain_text("Security")

    def test_security_has_key_storage(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/security")
        expect(page.locator("text=Key Storage")).to_be_visible()
        expect(page.locator("text=environment variables")).to_be_visible()

    def test_security_has_webhook_verification(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/security")
        expect(page.locator("text=Webhook Security")).to_be_visible()
        expect(page.locator("text=HMAC-SHA256")).to_be_visible()

    def test_security_has_code_example(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/security")
        # Should have the webhook verification code example
        expect(page.locator("text=verify_webhook")).to_be_visible()


class TestComplianceGuideDocs:
    def test_compliance_guide_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/compliance-guide")
        expect(page.locator("h1")).to_contain_text("Compliance Guide")

    def test_compliance_has_legal_framework(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/compliance-guide")
        expect(page.locator("text=Practicing Law")).to_be_visible()

    def test_compliance_has_boi_section(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/compliance-guide")
        expect(page.locator("text=Beneficial Ownership")).to_be_visible()
        expect(page.locator("text=FinCEN")).to_be_visible()

    def test_compliance_has_publication_states(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/compliance-guide")
        expect(page.locator("text=New York")).to_be_visible()
        expect(page.locator("text=Arizona")).to_be_visible()

    def test_compliance_has_launch_checklist(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/compliance-guide")
        expect(page.locator("text=Checklist for Launch")).to_be_visible()

    def test_compliance_has_disclaimers(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs/compliance-guide")
        expect(page.locator("text=Recommended Disclaimers")).to_be_visible()


class TestDocsNavigation:
    """Test navigation between documentation pages via sidebar."""

    def test_sidebar_nav_to_quickstart(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        page.locator(".docs-sidebar a[href='/docs/quickstart']").click()
        expect(page).to_have_url(re.compile(r"/docs/quickstart"))
        expect(page.locator("h1")).to_contain_text("Quickstart")

    def test_sidebar_nav_to_authentication(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        page.locator(".docs-sidebar a[href='/docs/authentication']").click()
        expect(page).to_have_url(re.compile(r"/docs/authentication"))

    def test_sidebar_nav_to_api_reference(self, page: Page, base_url: str):
        page.goto(f"{base_url}/docs")
        page.locator(".docs-sidebar a[href='/docs/api-reference']").click()
        expect(page).to_have_url(re.compile(r"/docs/api-reference"))

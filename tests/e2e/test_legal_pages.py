"""E2E tests: Verify all legal pages load with required content."""

import re
import pytest
from playwright.sync_api import Page, expect


class TestTermsOfService:
    def test_terms_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/terms")
        expect(page).to_have_title(re.compile(r"Terms"))
        expect(page.locator("h1")).to_contain_text("Terms of Service")

    def test_terms_has_not_law_firm_disclosure(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/terms")
        expect(page.locator("text=not a law firm")).to_be_visible()

    def test_terms_has_required_sections(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/terms")
        content = page.content()
        required_sections = [
            "Acceptance of Terms",
            "Description of Services",
            "Account Registration",
            "API Key Usage",
            "Fees and Payment",
            "Limitation of Liability",
            "Indemnification",
            "Termination",
            "Governing Law",
        ]
        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_terms_mentions_state_fees_non_refundable(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/terms")
        expect(page.locator("text=non-refundable")).to_be_visible()

    def test_terms_has_contact_info(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/terms")
        expect(page.locator("text=legal@formation.dev")).to_be_visible()


class TestPrivacyPolicy:
    def test_privacy_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/privacy")
        expect(page).to_have_title(re.compile(r"Privacy"))
        expect(page.locator("h1")).to_contain_text("Privacy Policy")

    def test_privacy_has_data_collection(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/privacy")
        expect(page.locator("text=Information We Collect")).to_be_visible()

    def test_privacy_has_data_usage(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/privacy")
        expect(page.locator("text=How We Use")).to_be_visible()

    def test_privacy_has_sharing_disclosure(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/privacy")
        expect(page.locator("text=not sell")).to_be_visible()

    def test_privacy_has_security_section(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/privacy")
        expect(page.locator("text=Data Security")).to_be_visible()
        expect(page.locator("text=AES-256")).to_be_visible()

    def test_privacy_has_ccpa(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/privacy")
        expect(page.locator("text=California Privacy")).to_be_visible()

    def test_privacy_has_retention_policy(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/privacy")
        expect(page.locator("text=Data Retention")).to_be_visible()

    def test_privacy_has_contact(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/privacy")
        expect(page.locator("text=privacy@formation.dev")).to_be_visible()


class TestSecurityPage:
    def test_security_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/security")
        expect(page).to_have_title(re.compile(r"Security"))
        expect(page.locator("h1")).to_contain_text("Security")

    def test_security_has_encryption(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/security")
        expect(page.locator("text=TLS 1.2")).to_be_visible()
        expect(page.locator("text=AES-256")).to_be_visible()

    def test_security_has_infrastructure(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/security")
        expect(page.locator("text=Infrastructure Security")).to_be_visible()

    def test_security_has_pci(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/security")
        expect(page.locator("text=PCI DSS")).to_be_visible()

    def test_security_has_vuln_reporting(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/security")
        expect(page.locator("text=Vulnerability Reporting")).to_be_visible()
        expect(page.locator("text=security@formation.dev")).to_be_visible()

    def test_security_has_incident_response(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/security")
        expect(page.locator("text=Incident Response")).to_be_visible()
        expect(page.locator("text=72 hours")).to_be_visible()


class TestCompliancePage:
    def test_compliance_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/compliance")
        expect(page).to_have_title(re.compile(r"Compliance"))
        expect(page.locator("h1")).to_contain_text("Compliance")

    def test_compliance_has_state_filing(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/compliance")
        expect(page.locator("text=State Formation Compliance")).to_be_visible()

    def test_compliance_has_fincen(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/compliance")
        expect(page.locator("text=FinCEN")).to_be_visible()

    def test_compliance_has_ccpa(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/compliance")
        expect(page.locator("text=CCPA")).to_be_visible()

    def test_compliance_has_not_law_firm(self, page: Page, base_url: str):
        page.goto(f"{base_url}/legal/compliance")
        expect(page.locator("text=not a law firm")).to_be_visible()

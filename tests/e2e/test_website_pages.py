"""E2E tests: Verify all website pages load correctly with proper content and SEO elements."""

import re
import pytest
from playwright.sync_api import Page, expect


class TestHomePage:
    """Test the landing page renders correctly with all SEO and content elements."""

    def test_home_loads(self, page: Page, base_url: str):
        page.goto(base_url)
        expect(page).to_have_title(re.compile(r"Business Formation"))

    def test_home_has_hero(self, page: Page, base_url: str):
        page.goto(base_url)
        hero = page.locator("section.hero")
        expect(hero).to_be_visible()
        expect(hero.locator("h1")).to_contain_text("Business Formation")

    def test_home_has_cta_buttons(self, page: Page, base_url: str):
        page.goto(base_url)
        expect(page.locator("a[href='/signup']").first).to_be_visible()
        expect(page.locator("a[href='/docs/quickstart']").first).to_be_visible()

    def test_home_has_code_example(self, page: Page, base_url: str):
        page.goto(base_url)
        code_block = page.locator(".code-block").first
        expect(code_block).to_be_visible()
        expect(code_block.locator("pre")).to_contain_text("curl")

    def test_home_has_stats(self, page: Page, base_url: str):
        page.goto(base_url)
        expect(page.locator(".stat").first).to_be_visible()
        expect(page.locator("text=50+")).to_be_visible()

    def test_home_has_feature_cards(self, page: Page, base_url: str):
        page.goto(base_url)
        cards = page.locator("section .card")
        assert cards.count() >= 6

    def test_home_has_footer(self, page: Page, base_url: str):
        page.goto(base_url)
        footer = page.locator("footer")
        expect(footer).to_be_visible()
        expect(footer.locator("text=Terms of Service")).to_be_visible()
        expect(footer.locator("text=Privacy Policy")).to_be_visible()

    def test_home_has_meta_description(self, page: Page, base_url: str):
        page.goto(base_url)
        meta = page.locator('meta[name="description"]')
        content = meta.get_attribute("content")
        assert content and len(content) > 50
        assert "formation" in content.lower() or "api" in content.lower()

    def test_home_has_open_graph(self, page: Page, base_url: str):
        page.goto(base_url)
        og_title = page.locator('meta[property="og:title"]')
        assert og_title.get_attribute("content")

    def test_home_has_structured_data(self, page: Page, base_url: str):
        page.goto(base_url)
        ld_json = page.locator('script[type="application/ld+json"]')
        expect(ld_json).to_be_attached()


class TestFeaturesPage:
    def test_features_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/features")
        expect(page).to_have_title(re.compile(r"Features"))
        expect(page.locator("h1")).to_contain_text("Features")

    def test_features_has_entity_info(self, page: Page, base_url: str):
        page.goto(f"{base_url}/features")
        expect(page.locator("text=Entity Formation")).to_be_visible()
        expect(page.locator("text=All 50 States")).to_be_visible()

    def test_features_has_state_table(self, page: Page, base_url: str):
        page.goto(f"{base_url}/features")
        table = page.locator("table")
        expect(table.first).to_be_visible()
        expect(page.locator("text=Delaware")).to_be_visible()


class TestPricingPage:
    def test_pricing_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/pricing")
        expect(page).to_have_title(re.compile(r"Pricing"))
        expect(page.locator("h1")).to_contain_text("Pricing")

    def test_pricing_has_all_plans(self, page: Page, base_url: str):
        page.goto(f"{base_url}/pricing")
        expect(page.locator("text=Free").first).to_be_visible()
        expect(page.locator("text=Starter").first).to_be_visible()
        expect(page.locator("text=Growth").first).to_be_visible()
        expect(page.locator("text=Enterprise").first).to_be_visible()

    def test_pricing_has_price_amounts(self, page: Page, base_url: str):
        page.goto(f"{base_url}/pricing")
        expect(page.locator("text=$0").first).to_be_visible()
        expect(page.locator("text=$49").first).to_be_visible()
        expect(page.locator("text=$199").first).to_be_visible()

    def test_pricing_has_faq(self, page: Page, base_url: str):
        page.goto(f"{base_url}/pricing")
        expect(page.locator("text=Frequently Asked Questions")).to_be_visible()


class TestAuthPages:
    def test_login_page_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/login")
        expect(page).to_have_title(re.compile(r"Sign In"))
        expect(page.locator("input[type='email']")).to_be_visible()
        expect(page.locator("input[type='password']")).to_be_visible()
        expect(page.locator("button[type='submit']")).to_be_visible()

    def test_login_has_signup_link(self, page: Page, base_url: str):
        page.goto(f"{base_url}/login")
        expect(page.locator("a[href='/signup']")).to_be_visible()

    def test_signup_page_loads(self, page: Page, base_url: str):
        page.goto(f"{base_url}/signup")
        expect(page).to_have_title(re.compile(r"Create Account"))
        expect(page.locator("input#full_name")).to_be_visible()
        expect(page.locator("input#email")).to_be_visible()
        expect(page.locator("input#password")).to_be_visible()

    def test_signup_has_tos_checkbox(self, page: Page, base_url: str):
        page.goto(f"{base_url}/signup")
        expect(page.locator("a[href='/legal/terms']")).to_be_visible()
        expect(page.locator("a[href='/legal/privacy']")).to_be_visible()

    def test_signup_has_login_link(self, page: Page, base_url: str):
        page.goto(f"{base_url}/signup")
        expect(page.locator("a[href='/login']")).to_be_visible()


class TestNavigation:
    """Test that navigation between pages works correctly."""

    def test_nav_to_features(self, page: Page, base_url: str):
        page.goto(base_url)
        page.click("a[href='/features']")
        expect(page).to_have_url(re.compile(r"/features"))
        expect(page.locator("h1")).to_contain_text("Features")

    def test_nav_to_pricing(self, page: Page, base_url: str):
        page.goto(base_url)
        page.click("a[href='/pricing']")
        expect(page).to_have_url(re.compile(r"/pricing"))
        expect(page.locator("h1")).to_contain_text("Pricing")

    def test_nav_to_docs(self, page: Page, base_url: str):
        page.goto(base_url)
        page.locator(".nav__links a[href='/docs']").click()
        expect(page).to_have_url(re.compile(r"/docs"))

    def test_nav_to_signup(self, page: Page, base_url: str):
        page.goto(base_url)
        page.locator(".nav__cta a[href='/signup']").click()
        expect(page).to_have_url(re.compile(r"/signup"))

    def test_cta_get_api_keys(self, page: Page, base_url: str):
        page.goto(base_url)
        page.locator(".hero__cta a[href='/signup']").click()
        expect(page).to_have_url(re.compile(r"/signup"))

    def test_footer_links(self, page: Page, base_url: str):
        page.goto(base_url)
        page.locator("footer a[href='/legal/terms']").click()
        expect(page).to_have_url(re.compile(r"/legal/terms"))

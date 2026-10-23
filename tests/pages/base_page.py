"""Base page object: navigation plus the header and flash messages shared by every screen.

Page objects expose locators and user-level actions; assertions live in the tests (via `expect`),
except for `expect_loaded`, which every page uses to confirm navigation landed where it should.
"""
import re

from playwright.sync_api import Locator, Page, expect


class BasePage:
    #: Path relative to the base URL. Subclasses override it.
    path = "/"
    #: Visible <h1> text (or pattern) that identifies the page.
    heading: str | re.Pattern = ""

    def __init__(self, page: Page):
        self.page = page
        self.nav_dashboard = page.get_by_test_id("nav-dashboard")
        self.nav_upload = page.get_by_test_id("nav-upload")
        self.current_user = page.get_by_test_id("current-user")
        self.logout_button = page.get_by_test_id("logout-button")
        self.flash_messages = page.get_by_test_id("flash-message")

    def open(self):
        self.page.goto(self.path)
        return self

    def expect_loaded(self):
        expect(self.page.get_by_role("heading", level=1, name=self.heading)).to_be_visible()
        return self

    def logout(self) -> None:
        self.logout_button.click()

    def text_of(self, locator: Locator) -> str:
        return locator.inner_text().strip()

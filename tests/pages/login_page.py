from playwright.sync_api import Page

from .base_page import BasePage


class LoginPage(BasePage):
    path = "/accounts/login/"
    heading = "Log in"

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.get_by_label("Username")
        self.password_input = page.get_by_label("Password")
        self.submit_button = page.get_by_test_id("login-submit")
        self.error = page.get_by_test_id("login-error")

    def login(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()

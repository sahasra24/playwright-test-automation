import re

import pytest
from playwright.sync_api import Page, expect

from tests.pages import DashboardPage, LoginPage


@pytest.mark.smoke
def test_valid_login_lands_on_dashboard(page: Page, credentials):
    LoginPage(page).open().login(**credentials)

    dashboard = DashboardPage(page).expect_loaded()
    expect(dashboard.current_user).to_have_text(credentials["username"])


@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param("qa_user", "wrong-password", id="wrong-password"),
        pytest.param("nobody", "qa-Passw0rd!", id="unknown-user"),
        pytest.param("QA_USER", "qa-Passw0rd!", id="username-case-sensitive"),
    ],
)
def test_invalid_login_shows_error(page: Page, username, password):
    login = LoginPage(page).open()
    login.login(username, password)

    expect(login.error).to_be_visible()
    login.expect_loaded()
    expect(login.current_user).to_have_count(0)


@pytest.mark.parametrize("path", ["/", "/upload/", "/runs/1/"])
def test_protected_pages_redirect_to_login(page: Page, path):
    page.goto(path)

    expect(page).to_have_url(re.compile(r"/accounts/login/\?next=" + re.escape(path)))
    LoginPage(page).expect_loaded()


def test_login_returns_to_requested_page(page: Page, credentials):
    page.goto("/upload/")
    LoginPage(page).login(**credentials)

    expect(page).to_have_url(re.compile(r"/upload/$"))


def test_logout_ends_session(page: Page, credentials):
    # Logs in separately: logging out of the shared auth_page session would break other tests.
    LoginPage(page).open().login(**credentials)
    DashboardPage(page).expect_loaded().logout()

    LoginPage(page).expect_loaded()
    page.goto("/")
    expect(page).to_have_url(re.compile(r"/accounts/login/"))

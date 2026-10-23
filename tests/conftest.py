"""Session setup for the whole suite.

By default the fixtures boot the Django app on a free local port against a throwaway SQLite
database, seed a login user, and tear it all down afterwards. Set BASE_URL to point the suite at an
already-running deployment instead (TEST_USERNAME / TEST_PASSWORD / VALIDATOR_API_KEY must match it).
"""
import base64
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import APIRequestContext, Browser, Page, Playwright

from tests.clients import ValidatorApi
from tests.pages import DashboardPage, LoginPage

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
REPORTS_DIR = ROOT / "reports"
DATA_DIR = Path(__file__).resolve().parent / "data"

TEST_USERNAME = os.environ.get("TEST_USERNAME", "qa_user")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "qa-Passw0rd!")
API_KEY = os.environ.get("VALIDATOR_API_KEY", "test-api-key")


def pytest_collection_modifyitems(items):
    # Tag tests by folder so `-m ui` / `-m api` work without decorating every test.
    for item in items:
        parts = Path(item.fspath).parts
        if "ui" in parts:
            item.add_marker(pytest.mark.ui)
        elif "api" in parts:
            item.add_marker(pytest.mark.api)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Embed a screenshot in the HTML report when a browser test fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("auth_page") or item.funcargs.get("page")
    if page is None or page.is_closed():
        return
    import pytest_html

    screenshot = base64.b64encode(page.screenshot(full_page=True)).decode()
    report.extras = [*getattr(report, "extras", []), pytest_html.extras.png(screenshot, "Failure screenshot")]


# --- Application under test -------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for(url: str, server: subprocess.Popen, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"Django server exited early; see {REPORTS_DIR / 'server.log'}")
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.25)
    raise RuntimeError(f"Django server did not answer {url} within {timeout}s")


@pytest.fixture(scope="session")
def base_url(tmp_path_factory):
    """Overrides pytest-base-url's fixture; pytest-playwright passes it to every browser context."""
    external = os.environ.get("BASE_URL")
    if external:
        yield external.rstrip("/")
        return

    env = {
        **os.environ,
        "DJANGO_DEBUG": "0",
        "DJANGO_DB_PATH": str(tmp_path_factory.mktemp("db") / "test.sqlite3"),
        "VALIDATOR_API_KEY": API_KEY,
        "PYTHONUNBUFFERED": "1",
    }
    manage = [sys.executable, "manage.py"]
    for command in (["migrate", "--noinput"], ["seed_user", "--username", TEST_USERNAME, "--password", TEST_PASSWORD]):
        subprocess.run([*manage, *command], cwd=APP_DIR, env=env, check=True, capture_output=True)

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    REPORTS_DIR.mkdir(exist_ok=True)
    with open(REPORTS_DIR / "server.log", "w") as log:
        server = subprocess.Popen(
            [*manage, "runserver", f"127.0.0.1:{port}", "--noreload"],
            cwd=APP_DIR, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            _wait_for(f"{url}/api/health/", server)
            yield url
        finally:
            server.terminate()
            server.wait(timeout=10)


@pytest.fixture(scope="session")
def credentials() -> dict[str, str]:
    return {"username": TEST_USERNAME, "password": TEST_PASSWORD}


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return DATA_DIR


# --- Browser ------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def auth_state(browser: Browser, base_url: str, credentials, tmp_path_factory) -> str:
    """Log in once per session through the real UI and save the cookies for reuse."""
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    LoginPage(page).open().login(**credentials)
    DashboardPage(page).expect_loaded()
    path = tmp_path_factory.mktemp("auth") / "state.json"
    context.storage_state(path=path)
    context.close()
    return str(path)


@pytest.fixture
def auth_page(new_context, auth_state) -> Page:
    """A fresh, already logged-in page. Uses pytest-playwright's tracing/screenshot handling."""
    return new_context(storage_state=auth_state).new_page()


# --- API ----------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def api_request_context(playwright: Playwright, base_url: str):
    context = playwright.request.new_context(base_url=base_url, extra_http_headers={"X-API-Key": API_KEY})
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def anonymous_request_context(playwright: Playwright, base_url: str):
    context = playwright.request.new_context(base_url=base_url)
    yield context
    context.dispose()


@pytest.fixture
def api(api_request_context: APIRequestContext) -> ValidatorApi:
    return ValidatorApi(api_request_context)


@pytest.fixture
def anonymous_api(anonymous_request_context: APIRequestContext) -> ValidatorApi:
    return ValidatorApi(anonymous_request_context)

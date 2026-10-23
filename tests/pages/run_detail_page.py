import re

from playwright.sync_api import Page, expect

from .base_page import BasePage

RUN_URL = re.compile(r"/runs/(\d+)/$")


class RunDetailPage(BasePage):
    heading = re.compile(r"^Run #\d+$")

    def __init__(self, page: Page, run_id: int | None = None):
        super().__init__(page)
        if run_id is not None:
            self.path = f"/runs/{run_id}/"
        self.filename = page.get_by_test_id("run-filename")
        self.status = page.get_by_test_id("run-status")
        self.total_rows = page.get_by_test_id("total-rows")
        self.valid_rows = page.get_by_test_id("valid-rows")
        self.invalid_rows = page.get_by_test_id("invalid-rows")
        self.error_rows = page.get_by_test_id("error-row")
        self.no_errors = page.get_by_test_id("no-errors")

    def expect_loaded(self):
        expect(self.page).to_have_url(RUN_URL)
        return super().expect_loaded()

    @property
    def run_id(self) -> int:
        match = RUN_URL.search(self.page.url)
        assert match, f"Not on a run page: {self.page.url}"
        return int(match.group(1))

    def errors(self) -> list[tuple[int, str, str]]:
        """Return the errors table as (row, field, message) tuples, in display order."""
        return [
            (
                int(self.text_of(row.get_by_test_id("error-row-number"))),
                self.text_of(row.get_by_test_id("error-field")),
                self.text_of(row.get_by_test_id("error-message")),
            )
            for row in self.error_rows.all()
        ]

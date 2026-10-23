from playwright.sync_api import Locator, Page

from .base_page import BasePage


class DashboardPage(BasePage):
    path = "/"
    heading = "Validation runs"

    def __init__(self, page: Page):
        super().__init__(page)
        self.new_upload_button = page.get_by_test_id("new-upload")
        self.runs_table = page.get_by_test_id("runs-table")
        self.run_rows = page.get_by_test_id("run-row")
        self.empty_state = page.get_by_test_id("empty-state")

    def row_for_run(self, run_id: int) -> Locator:
        return self.page.locator(f'[data-testid="run-row"][data-run-id="{run_id}"]')

    def open_run(self, run_id: int) -> None:
        self.row_for_run(run_id).get_by_test_id("run-link").click()

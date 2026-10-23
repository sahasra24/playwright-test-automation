from pathlib import Path

from playwright.sync_api import Page

from .base_page import BasePage


class UploadPage(BasePage):
    path = "/upload/"
    heading = "Validate a customer file"

    def __init__(self, page: Page):
        super().__init__(page)
        self.file_input = page.get_by_label("CSV file")
        self.submit_button = page.get_by_test_id("upload-submit")
        self.form_errors = page.get_by_test_id("form-error")

    def upload(self, file: Path | str) -> None:
        self.file_input.set_input_files(file)
        self.submit_button.click()

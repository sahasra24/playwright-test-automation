import pytest
from playwright.sync_api import Page, expect

from tests.pages import DashboardPage, RunDetailPage, UploadPage
from tests.utils.records import BOUNDARY_VALID_CASES, COLUMNS, INVALID_FIELD_CASES, make_record, write_csv


@pytest.fixture
def upload_page(auth_page: Page) -> UploadPage:
    return UploadPage(auth_page).open().expect_loaded()


@pytest.mark.smoke
def test_valid_file_passes(upload_page: UploadPage, data_dir):
    upload_page.upload(data_dir / "valid_customers.csv")

    run = RunDetailPage(upload_page.page).expect_loaded()
    expect(run.flash_messages).to_have_text("Validated 5 rows from valid_customers.csv.")
    expect(run.status).to_have_text("passed")
    expect(run.total_rows).to_have_text("5")
    expect(run.valid_rows).to_have_text("5")
    expect(run.invalid_rows).to_have_text("0")
    expect(run.no_errors).to_be_visible()


def test_invalid_file_lists_every_row_error(upload_page: UploadPage, data_dir):
    upload_page.upload(data_dir / "invalid_customers.csv")

    run = RunDetailPage(upload_page.page).expect_loaded()
    expect(run.status).to_have_text("failed")
    expect(run.total_rows).to_have_text("5")
    expect(run.valid_rows).to_have_text("1")
    expect(run.invalid_rows).to_have_text("4")
    assert run.errors() == [
        (2, "name", "Name is required"),
        (3, "email", "Email is not a valid address"),
        (4, "id", "Duplicate ID (first seen in row 1)"),
        (4, "age", "Age must be between 0 and 120"),
        (5, "country", "Country must be a 2-letter uppercase ISO code"),
        (5, "signup_date", "Signup date must use the YYYY-MM-DD format"),
    ]


@pytest.mark.parametrize("field, value, message", INVALID_FIELD_CASES)
def test_single_field_rule_is_reported(upload_page: UploadPage, tmp_path, field, value, message):
    records = [make_record(), make_record(**{field: value})]
    upload_page.upload(write_csv(tmp_path / "customers.csv", records))

    run = RunDetailPage(upload_page.page).expect_loaded()
    expect(run.invalid_rows).to_have_text("1")
    assert run.errors() == [(2, field, message)]


@pytest.mark.parametrize("field, value", BOUNDARY_VALID_CASES)
def test_boundary_values_pass(upload_page: UploadPage, tmp_path, field, value):
    upload_page.upload(write_csv(tmp_path / "customers.csv", [make_record(**{field: value})]))

    run = RunDetailPage(upload_page.page).expect_loaded()
    expect(run.status).to_have_text("passed")


@pytest.mark.parametrize(
    "filename, message",
    [
        pytest.param("missing_columns.csv", "Missing required column(s): email", id="missing-column"),
        pytest.param("header_only.csv", "File has a header row but no data rows.", id="header-only"),
    ],
)
def test_unusable_file_is_rejected(upload_page: UploadPage, data_dir, filename, message):
    upload_page.upload(data_dir / filename)

    expect(upload_page.form_errors).to_have_text(message)
    upload_page.expect_loaded()


def test_non_csv_file_is_rejected(upload_page: UploadPage, tmp_path):
    text_file = tmp_path / "customers.txt"
    text_file.write_text(",".join(COLUMNS))

    upload_page.upload(text_file)

    expect(upload_page.form_errors).to_have_text("Only .csv files are accepted.")


def test_non_utf8_file_is_rejected(upload_page: UploadPage, tmp_path):
    latin1_file = tmp_path / "customers.csv"
    latin1_file.write_bytes(",".join(COLUMNS).encode() + b"\n1,Jos\xe9,j@example.com,30,ES,2024-01-01\n")

    upload_page.upload(latin1_file)

    expect(upload_page.form_errors).to_have_text("File must be a UTF-8 encoded CSV.")


def test_new_run_appears_on_dashboard(upload_page: UploadPage, data_dir):
    upload_page.upload(data_dir / "invalid_customers.csv")
    run_id = RunDetailPage(upload_page.page).expect_loaded().run_id

    dashboard = DashboardPage(upload_page.page)
    dashboard.nav_dashboard.click()
    dashboard.expect_loaded()

    row = dashboard.row_for_run(run_id)
    expect(dashboard.run_rows.first).to_have_attribute("data-run-id", str(run_id))
    expect(row.get_by_test_id("run-filename")).to_have_text("invalid_customers.csv")
    expect(row.get_by_test_id("run-invalid")).to_have_text("4")
    expect(row.get_by_test_id("run-status")).to_have_text("failed")

    dashboard.open_run(run_id)
    assert RunDetailPage(upload_page.page).expect_loaded().run_id == run_id

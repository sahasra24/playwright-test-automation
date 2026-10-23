"""Validation rules for customer records, independent of Django so they are easy to reason about.

A record is a mapping with the columns in REQUIRED_COLUMNS. Every rule failure becomes a FieldError
tagged with the 1-based data row it came from; a row is invalid if it has at least one error.
"""
import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

REQUIRED_COLUMNS = ("id", "name", "email", "age", "country", "signup_date")

LABELS = {
    "id": "ID",
    "name": "Name",
    "email": "Email",
    "age": "Age",
    "country": "Country",
    "signup_date": "Signup date",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
MAX_NAME_LENGTH = 100
MIN_AGE, MAX_AGE = 0, 120


class SchemaError(Exception):
    """The input as a whole is unusable (wrong columns, empty file, bad encoding...)."""


@dataclass(frozen=True)
class FieldError:
    row: int
    field: str
    message: str


@dataclass
class ValidationResult:
    total_rows: int
    errors: list[FieldError] = field(default_factory=list)

    @property
    def invalid_rows(self) -> int:
        return len({error.row for error in self.errors})

    @property
    def valid_rows(self) -> int:
        return self.total_rows - self.invalid_rows


def parse_csv(raw: bytes, max_rows: int) -> list[dict[str, str]]:
    """Decode an uploaded CSV into records, raising SchemaError if it can't be validated row by row."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SchemaError("File must be a UTF-8 encoded CSV.") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise SchemaError("File is empty.")

    columns = [name.strip() for name in reader.fieldnames]
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise SchemaError(f"Missing required column(s): {', '.join(missing)}")

    # Short rows yield None values and long rows a None key; both are normalised away here.
    records = [
        {key.strip(): value for key, value in row.items() if key is not None}
        for row in reader
    ]
    if not records:
        raise SchemaError("File has a header row but no data rows.")
    if len(records) > max_rows:
        raise SchemaError(f"File has {len(records)} rows; the limit is {max_rows}.")
    return records


def validate_records(records: list[dict]) -> ValidationResult:
    result = ValidationResult(total_rows=len(records))
    first_row_for_id: dict[str, int] = {}
    for row_number, record in enumerate(records, start=1):
        result.errors.extend(_validate_record(row_number, record, first_row_for_id))
    return result


def _validate_record(row: int, record: dict, first_row_for_id: dict[str, int]) -> list[FieldError]:
    values = {column: _as_text(record.get(column)) for column in REQUIRED_COLUMNS}
    errors = [
        FieldError(row, column, f"{LABELS[column]} is required")
        for column, value in values.items()
        if value == ""
    ]

    def fail(column: str, message: str) -> None:
        errors.append(FieldError(row, column, message))

    record_id = values["id"]
    if record_id:
        if not record_id.isdigit() or int(record_id) == 0:
            fail("id", "ID must be a positive whole number")
        elif record_id in first_row_for_id:
            fail("id", f"Duplicate ID (first seen in row {first_row_for_id[record_id]})")
        else:
            first_row_for_id[record_id] = row

    name = values["name"]
    if len(name) > MAX_NAME_LENGTH:
        fail("name", f"Name must be at most {MAX_NAME_LENGTH} characters")

    email = values["email"]
    if email and not EMAIL_RE.match(email):
        fail("email", "Email is not a valid address")

    age = values["age"]
    if age:
        if not age.lstrip("-").isdigit():
            fail("age", "Age must be a whole number")
        elif not MIN_AGE <= int(age) <= MAX_AGE:
            fail("age", f"Age must be between {MIN_AGE} and {MAX_AGE}")

    country = values["country"]
    if country and not COUNTRY_RE.match(country):
        fail("country", "Country must be a 2-letter uppercase ISO code")

    signup_date = values["signup_date"]
    if signup_date:
        try:
            parsed = datetime.strptime(signup_date, "%Y-%m-%d").date()
        except ValueError:
            fail("signup_date", "Signup date must use the YYYY-MM-DD format")
        else:
            if parsed > datetime.now(timezone.utc).date():
                fail("signup_date", "Signup date cannot be in the future")

    return errors


def _as_text(value) -> str:
    # JSON payloads may carry numbers; keep 0 as "0" rather than treating it as missing.
    return "" if value is None else str(value).strip()

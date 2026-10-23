"""Test data builders and the rule cases shared by the UI and API suites."""
import csv
import itertools
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

COLUMNS = ["id", "name", "email", "age", "country", "signup_date"]

_ids = itertools.count(1)


def make_record(**overrides) -> dict:
    """A record that passes every rule, with a fresh id each call. Overrides replace fields."""
    n = next(_ids)
    record = {
        "id": str(n),
        "name": f"Customer {n}",
        "email": f"customer{n}@example.com",
        "age": "34",
        "country": "US",
        "signup_date": "2024-03-15",
    }
    record.update(overrides)
    return record


def write_csv(path: Path, records: list[dict], columns: list[str] = COLUMNS) -> Path:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    return path


# The app judges "future" dates in UTC, so the tests must too.
TODAY = datetime.now(timezone.utc).date()
TOMORROW = (TODAY + timedelta(days=1)).isoformat()

# (field, bad value, expected message): one broken field in an otherwise valid record.
INVALID_FIELD_CASES = [
    pytest.param("id", "", "ID is required", id="id-missing"),
    pytest.param("id", "abc", "ID must be a positive whole number", id="id-not-numeric"),
    pytest.param("id", "0", "ID must be a positive whole number", id="id-zero"),
    pytest.param("name", "", "Name is required", id="name-missing"),
    pytest.param("name", "x" * 101, "Name must be at most 100 characters", id="name-too-long"),
    pytest.param("email", "not-an-email", "Email is not a valid address", id="email-no-at"),
    pytest.param("email", "a@b", "Email is not a valid address", id="email-no-tld"),
    pytest.param("age", "thirty", "Age must be a whole number", id="age-not-numeric"),
    pytest.param("age", "-1", "Age must be between 0 and 120", id="age-below-min"),
    pytest.param("age", "121", "Age must be between 0 and 120", id="age-above-max"),
    pytest.param("country", "usa", "Country must be a 2-letter uppercase ISO code", id="country-bad"),
    pytest.param("signup_date", "15/03/2024", "Signup date must use the YYYY-MM-DD format", id="date-format"),
    pytest.param("signup_date", "2024-02-30", "Signup date must use the YYYY-MM-DD format", id="date-impossible"),
    pytest.param("signup_date", TOMORROW, "Signup date cannot be in the future", id="date-future"),
]

# Values on the edge of a rule that must still pass.
BOUNDARY_VALID_CASES = [
    pytest.param("age", "0", id="age-min"),
    pytest.param("age", "120", id="age-max"),
    pytest.param("name", "x" * 100, id="name-max-length"),
    pytest.param("signup_date", TODAY.isoformat(), id="date-today"),
]

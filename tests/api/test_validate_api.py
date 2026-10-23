import pytest

from tests.utils.records import BOUNDARY_VALID_CASES, INVALID_FIELD_CASES, make_record


@pytest.mark.smoke
def test_valid_records_pass(api):
    response = api.validate([make_record() for _ in range(3)], name="batch-1")

    assert response.status == 201
    body = response.json()
    assert body["status"] == "passed"
    assert body["source"] == "api"
    assert body["filename"] == "batch-1"
    assert (body["total_rows"], body["valid_rows"], body["invalid_rows"]) == (3, 3, 0)
    assert body["errors"] == []


def test_mixed_records_report_only_failing_rows(api):
    records = [make_record(), make_record(email="broken"), make_record(), make_record(age="200", country="xx")]

    body = api.validate(records).json()

    assert body["status"] == "failed"
    assert (body["total_rows"], body["valid_rows"], body["invalid_rows"]) == (4, 2, 2)
    assert body["errors"] == [
        {"row": 2, "field": "email", "message": "Email is not a valid address"},
        {"row": 4, "field": "age", "message": "Age must be between 0 and 120"},
        {"row": 4, "field": "country", "message": "Country must be a 2-letter uppercase ISO code"},
    ]


@pytest.mark.parametrize("field, value, message", INVALID_FIELD_CASES)
def test_single_field_rule_is_reported(api, field, value, message):
    body = api.validate([make_record(**{field: value})]).json()

    assert body["errors"] == [{"row": 1, "field": field, "message": message}]


@pytest.mark.parametrize("field, value", BOUNDARY_VALID_CASES)
def test_boundary_values_pass(api, field, value):
    body = api.validate([make_record(**{field: value})]).json()

    assert body["status"] == "passed", body["errors"]


def test_json_numbers_are_accepted(api):
    record = make_record(id=7, age=0)

    body = api.validate([record]).json()

    assert body["status"] == "passed", body["errors"]


def test_missing_and_null_fields_are_required(api):
    record = make_record(email=None)
    del record["country"]

    body = api.validate([record]).json()

    assert body["errors"] == [
        {"row": 1, "field": "email", "message": "Email is required"},
        {"row": 1, "field": "country", "message": "Country is required"},
    ]


def test_duplicate_ids_point_to_first_occurrence(api):
    records = [make_record(id="10"), make_record(), make_record(id="10"), make_record(id="10")]

    body = api.validate(records).json()

    assert body["errors"] == [
        {"row": 3, "field": "id", "message": "Duplicate ID (first seen in row 1)"},
        {"row": 4, "field": "id", "message": "Duplicate ID (first seen in row 1)"},
    ]


@pytest.mark.parametrize(
    "body, message",
    [
        pytest.param("not json", "Request body must be valid JSON.", id="not-json"),
        pytest.param("[]", '"records" must be a list of objects.', id="top-level-list"),
        pytest.param("{}", '"records" must be a list of objects.', id="records-missing"),
        pytest.param('{"records": "x"}', '"records" must be a list of objects.', id="records-string"),
        pytest.param('{"records": [1, 2]}', '"records" must be a list of objects.', id="records-not-objects"),
        pytest.param('{"records": []}', '"records" must not be empty.', id="records-empty"),
    ],
)
def test_malformed_payload_is_rejected(api, body, message):
    response = api.validate_raw(body)

    assert response.status == 400
    assert response.json() == {"error": message}


def test_validate_rejects_get(api_request_context):
    response = api_request_context.get("/api/validate/")

    assert response.status == 405

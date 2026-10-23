from tests.utils.records import make_record


def test_created_run_is_listed_first(api):
    created = api.validate([make_record()], name="listed-run").json()

    response = api.list_runs()

    assert response.status == 200
    latest = response.json()["runs"][0]
    assert latest["id"] == created["id"]
    assert latest["filename"] == "listed-run"
    assert "errors" not in latest


def test_run_detail_matches_validation_response(api):
    created = api.validate([make_record(), make_record(age="abc")]).json()

    response = api.get_run(created["id"])

    assert response.status == 200
    assert response.json() == created


def test_unknown_run_returns_404(api):
    response = api.get_run(999_999)

    assert response.status == 404
    assert response.json() == {"error": "Run not found."}

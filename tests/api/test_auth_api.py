import pytest
from playwright.sync_api import APIRequestContext

PROTECTED_ENDPOINTS = [
    pytest.param("POST", "/api/validate/", id="validate"),
    pytest.param("GET", "/api/runs/", id="run-list"),
    pytest.param("GET", "/api/runs/1/", id="run-detail"),
]


@pytest.mark.smoke
def test_health_is_public(anonymous_api):
    response = anonymous_api.health()

    assert response.status == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("method, path", PROTECTED_ENDPOINTS)
@pytest.mark.parametrize("api_key", [None, "wrong-key"], ids=["no-key", "wrong-key"])
def test_protected_endpoints_require_api_key(
    anonymous_request_context: APIRequestContext, method, path, api_key
):
    headers = {"X-API-Key": api_key} if api_key else {}
    data = {"records": []} if method == "POST" else None
    response = anonymous_request_context.fetch(path, method=method, headers=headers, data=data)

    assert response.status == 401
    assert response.json() == {"error": "Invalid or missing API key."}

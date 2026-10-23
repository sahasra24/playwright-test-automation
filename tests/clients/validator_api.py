"""Thin client over Playwright's APIRequestContext: the API-layer counterpart of the page objects.

Methods return the raw APIResponse so tests can assert on status codes as well as bodies.
"""
from playwright.sync_api import APIRequestContext, APIResponse


class ValidatorApi:
    def __init__(self, request: APIRequestContext):
        self.request = request

    def health(self) -> APIResponse:
        return self.request.get("/api/health/")

    def validate(self, records: list[dict], name: str | None = None) -> APIResponse:
        payload: dict = {"records": records}
        if name is not None:
            payload["name"] = name
        return self.request.post("/api/validate/", data=payload)

    def validate_raw(self, body: str) -> APIResponse:
        """Send a body verbatim, for malformed-payload tests."""
        # Bytes, not str: Playwright JSON-encodes a str body when the content type is JSON.
        return self.request.post(
            "/api/validate/", data=body.encode(), headers={"Content-Type": "application/json"}
        )

    def list_runs(self) -> APIResponse:
        return self.request.get("/api/runs/")

    def get_run(self, run_id: int) -> APIResponse:
        return self.request.get(f"/api/runs/{run_id}/")

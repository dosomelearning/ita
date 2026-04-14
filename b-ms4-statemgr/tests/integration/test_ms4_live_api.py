import json
import os
import urllib.error
import urllib.request

import pytest


BASE_URL = os.getenv("MS4_API_BASE_URL", "").rstrip("/")
JWT_TOKEN = os.getenv("MS4_TEST_JWT", "")


pytestmark = pytest.mark.skipif(
    not BASE_URL,
    reason="Set MS4_API_BASE_URL to run live integration tests.",
)


def _request(path: str):
    headers = {"Accept": "application/json"}
    if JWT_TOKEN:
        headers["Authorization"] = f"Bearer {JWT_TOKEN}"
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, body


def test_status_endpoint_returns_json_error_envelope_for_missing_upload():
    status_code, body = _request("/v1/uploads/integration-missing-id/status")
    assert status_code in {401, 403, 404}
    payload = json.loads(body)
    if status_code == 404:
        assert payload["error"]["code"] == "UPLOAD_NOT_FOUND"
        assert "requestId" in payload
        assert "timestamp" in payload

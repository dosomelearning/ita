import json

from src.api import Ms4Api
from src.domain import DomainError


class StubService:
    def __init__(self):
        self.calls = []

    def register_upload_init(self, payload):
        self.calls.append(("init", payload))
        return {"uploadId": payload["uploadId"], "status": "queued", "updatedAt": "2026-04-14T10:00:00Z"}

    def record_processing_event(self, upload_id, payload):
        self.calls.append(("event", upload_id, payload))
        return {"uploadId": upload_id, "status": payload["statusAfter"], "updatedAt": "2026-04-14T10:01:00Z"}

    def get_status(self, upload_id):
        self.calls.append(("status", upload_id))
        if upload_id == "missing":
            raise DomainError(
                code="UPLOAD_NOT_FOUND",
                message="Upload state not found.",
                status_code=404,
                details={"uploadId": upload_id},
            )
        return {"uploadId": upload_id, "status": "processing", "updatedAt": "2026-04-14T10:02:00Z"}


def make_http_event(method: str, path: str, body: str | None = None):
    return {
        "requestContext": {"http": {"method": method}, "requestId": "req-123"},
        "rawPath": path,
        "body": body,
    }


def test_post_internal_init_route():
    api = Ms4Api(StubService())
    event = make_http_event(
        "POST",
        "/internal/uploads/init",
        body=json.dumps(
            {
                "uploadId": "u-1",
                "sessionId": "s-1",
                "submittedAt": "2026-04-14T10:00:00Z",
                "source": "spa",
            }
        ),
    )
    response = api.handle(event, None)
    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["uploadId"] == "u-1"
    assert payload["status"] == "queued"


def test_post_internal_event_route():
    api = Ms4Api(StubService())
    event = make_http_event(
        "POST",
        "/internal/uploads/u-1/events",
        body=json.dumps(
            {
                "eventType": "detection_completed",
                "eventTime": "2026-04-14T10:01:00Z",
                "producer": "ms2",
                "statusAfter": "processing",
                "details": {},
            }
        ),
    )
    response = api.handle(event, None)
    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["uploadId"] == "u-1"
    assert payload["status"] == "processing"


def test_get_status_route():
    api = Ms4Api(StubService())
    event = make_http_event("GET", "/v1/uploads/u-1/status")
    response = api.handle(event, None)
    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["uploadId"] == "u-1"


def test_error_envelope_for_domain_error():
    api = Ms4Api(StubService())
    event = make_http_event("GET", "/v1/uploads/missing/status")
    response = api.handle(event, None)
    assert response["statusCode"] == 404
    payload = json.loads(response["body"])
    assert payload["error"]["code"] == "UPLOAD_NOT_FOUND"
    assert payload["requestId"] == "req-123"


def test_invalid_json_returns_validation_error():
    api = Ms4Api(StubService())
    event = make_http_event("POST", "/internal/uploads/init", body="{")
    response = api.handle(event, None)
    assert response["statusCode"] == 400
    payload = json.loads(response["body"])
    assert payload["error"]["code"] == "VALIDATION_ERROR"

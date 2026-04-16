import json

from src.api import IngressApi
from src.domain import IngressError


class StubService:
    def handle_upload_init(self, payload):
        if payload.get("password") == "bad":
            raise IngressError(
                code="INVALID_PASSWORD",
                message="Invalid class code. Ask instructor for current code.",
                status_code=401,
            )
        return {
            "accepted": True,
            "uploadId": "upl-1",
            "classRunId": "cr-demo",
            "uploadUrl": "https://example",
            "uploadMethod": "PUT",
            "uploadHeaders": {"Content-Type": "image/jpeg"},
            "objectKey": "uploaded/s-1/upl-1.jpg",
            "expiresInSeconds": 900,
        }


def make_event(method: str, path: str, body: str | None = None):
    return {
        "requestContext": {"http": {"method": method}, "requestId": "req-1"},
        "rawPath": path,
        "body": body,
    }


def test_upload_init_route_success():
    api = IngressApi(StubService())
    event = make_event(
        "POST",
        "/v1/uploads/init",
        body=json.dumps(
            {
                "password": "AB12CD",
                "nickname": "ava",
                "sessionId": "s-1",
                "contentType": "image/jpeg",
            }
        ),
    )
    response = api.handle(event, None)
    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["accepted"] is True
    assert payload["uploadId"] == "upl-1"


def test_upload_init_route_invalid_password_error():
    api = IngressApi(StubService())
    event = make_event(
        "POST",
        "/v1/uploads/init",
        body=json.dumps(
            {
                "password": "bad",
                "nickname": "ava",
                "sessionId": "s-1",
                "contentType": "image/jpeg",
            }
        ),
    )
    response = api.handle(event, None)
    assert response["statusCode"] == 401
    payload = json.loads(response["body"])
    assert payload["error"]["code"] == "INVALID_PASSWORD"


def test_route_not_found():
    api = IngressApi(StubService())
    response = api.handle(make_event("GET", "/v1/unknown"), None)
    assert response["statusCode"] == 404
    payload = json.loads(response["body"])
    assert payload["error"]["code"] == "NOT_FOUND"

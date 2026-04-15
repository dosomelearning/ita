from __future__ import annotations

import pytest

from src.domain import IngressError
from src.service import IngressService


class FakeSsmClient:
    def __init__(self, value: str = "class2026"):
        self.value = value

    def get_parameter(self, Name: str, WithDecryption: bool):
        _ = Name
        _ = WithDecryption
        return {"Parameter": {"Value": self.value}}


class FakeS3Client:
    def generate_presigned_url(self, ClientMethod, Params, ExpiresIn, HttpMethod):
        return (
            f"https://example-s3.local/presigned?"
            f"method={ClientMethod}&bucket={Params['Bucket']}&key={Params['Key']}&ct={Params['ContentType']}&exp={ExpiresIn}&http={HttpMethod}"
        )


class FakeMs4Client:
    def __init__(self, status: int = 200, payload: dict | None = None):
        self.status = status
        self.payload = payload or {}
        self.init_calls: list[dict] = []
        self.event_calls: list[tuple[str, dict]] = []

    def register_upload_init(self, payload):
        self.init_calls.append(payload)
        return self.status, self.payload

    def post_event(self, *, upload_id: str, payload: dict):
        self.event_calls.append((upload_id, payload))
        return self.status, self.payload


def make_service(*, password: str = "class2026", ms4_status: int = 200, ms4_payload: dict | None = None):
    return IngressService(
        shared_password_parameter_name="/ita/shared-password",
        processing_bucket_name="ita-data-bucket",
        presign_expires_seconds=900,
        ssm_client=FakeSsmClient(value=password),
        s3_client=FakeS3Client(),
        ms4_client=FakeMs4Client(status=ms4_status, payload=ms4_payload),
    )


def test_handle_upload_init_success():
    service = make_service()
    result = service.handle_upload_init(
        {
            "password": "class2026",
            "nickname": "ava",
            "sessionId": "s-1",
            "contentType": "image/jpeg",
        }
    )
    assert result["accepted"] is True
    assert result["uploadId"].startswith("upl-")
    assert result["classRunId"].startswith("cr-")
    assert result["objectKey"].startswith(f"uploaded/{result['classRunId']}/")
    assert result["uploadMethod"] == "PUT"
    assert "uploadUrl" in result


def test_handle_upload_init_emits_ms1_sequence_events():
    ms4_client = FakeMs4Client()
    service = IngressService(
        shared_password_parameter_name="/ita/shared-password",
        processing_bucket_name="ita-data-bucket",
        presign_expires_seconds=900,
        ssm_client=FakeSsmClient(value="class2026"),
        s3_client=FakeS3Client(),
        ms4_client=ms4_client,
    )

    service.handle_upload_init(
        {
            "password": "class2026",
            "nickname": "ava",
            "sessionId": "s-1",
            "contentType": "image/jpeg",
        }
    )

    assert len(ms4_client.init_calls) == 1
    assert len(ms4_client.event_calls) == 2
    assert ms4_client.event_calls[0][1]["eventType"] == "upload_init_received"
    assert ms4_client.event_calls[0][1]["statusAfter"] == "queued"
    assert ms4_client.event_calls[0][1]["producer"] == "ms1"
    assert ms4_client.event_calls[0][1]["details"]["uploadReady"] is False
    assert ms4_client.event_calls[1][1]["eventType"] == "upload_url_issued"
    assert ms4_client.event_calls[1][1]["details"]["uploadReady"] is True


def test_handle_upload_init_rejects_invalid_password():
    service = make_service()
    with pytest.raises(IngressError) as exc:
        service.handle_upload_init(
            {
                "password": "wrong",
                "nickname": "ava",
                "sessionId": "s-1",
                "contentType": "image/jpeg",
            }
        )
    assert exc.value.code == "INVALID_PASSWORD"
    assert exc.value.status_code == 401


def test_handle_upload_init_fails_when_ms4_init_fails():
    service = make_service(
        ms4_status=503,
        ms4_payload={"error": {"message": "MS4 unavailable"}},
    )
    with pytest.raises(IngressError) as exc:
        service.handle_upload_init(
            {
                "password": "class2026",
                "nickname": "ava",
                "sessionId": "s-1",
                "contentType": "image/jpeg",
            }
        )
    assert exc.value.code == "DEPENDENCY_UNAVAILABLE"
    assert exc.value.status_code == 503

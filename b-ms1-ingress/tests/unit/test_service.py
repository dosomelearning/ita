from __future__ import annotations

import pytest

from src.domain import IngressError
from src.service import IngressService


class FakeSsmClient:
    def __init__(self, value: str = "class2026", should_fail: bool = False):
        self.value = value
        self.should_fail = should_fail

    def get_parameter(self, Name: str, WithDecryption: bool):
        _ = Name
        _ = WithDecryption
        if self.should_fail:
            raise RuntimeError("ssm failure")
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
        self.calls: list[dict] = []

    def register_upload_init(self, payload):
        self.calls.append(payload)
        return self.status, self.payload


def make_service(*, ssm_value: str = "class2026", ms4_status: int = 200, ms4_payload: dict | None = None):
    return IngressService(
        shared_password_parameter_name="/ita/shared-password",
        processing_bucket_name="ita-data-bucket",
        presign_expires_seconds=900,
        ssm_client=FakeSsmClient(value=ssm_value),
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
    assert result["objectKey"].startswith("uploaded/s-1/")
    assert result["uploadMethod"] == "PUT"
    assert "uploadUrl" in result


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

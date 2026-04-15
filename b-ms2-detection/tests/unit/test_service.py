from __future__ import annotations

import json

import pytest
from botocore.exceptions import ClientError

from src.domain import DetectionError
from src.service import DetectionService


class FakeRekognitionClient:
    def __init__(self, *, face_details: list[dict] | None = None, fail: bool = False):
        self.face_details = face_details or []
        self.fail = fail

    def detect_faces(self, **kwargs):
        _ = kwargs
        if self.fail:
            raise ClientError({"Error": {"Code": "ThrottlingException", "Message": "throttle"}}, "DetectFaces")
        return {"FaceDetails": self.face_details}


class FakeS3Client:
    def __init__(self):
        self.put_calls: list[dict] = []
        self.copy_calls: list[dict] = []
        self.delete_calls: list[dict] = []

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)

    def copy_object(self, **kwargs):
        self.copy_calls.append(kwargs)

    def delete_object(self, **kwargs):
        self.delete_calls.append(kwargs)


class FakeSqsClient:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.messages: list[dict] = []

    def send_message(self, **kwargs):
        if self.fail:
            raise ClientError({"Error": {"Code": "ServiceUnavailable", "Message": "down"}}, "SendMessage")
        self.messages.append(kwargs)
        return {"MessageId": "m-1"}


class FakeMs4Client:
    def __init__(self, *, status: int = 200):
        self.status = status
        self.calls: list[tuple[str, dict]] = []

    def post_event(self, *, upload_id: str, payload: dict):
        self.calls.append((upload_id, payload))
        return self.status, {"ok": self.status < 300}


def _s3_event_body(key: str = "uploaded/s-1/upl-1.jpg") -> str:
    return json.dumps(
        {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "bucket": {"name": "ita-data-bucket"},
                        "object": {"key": key},
                    },
                }
            ]
        }
    )


def make_service(*, faces: list[dict] | None = None, rek_fail: bool = False, ms4_status: int = 200):
    return DetectionService(
        processing_bucket_name="ita-data-bucket",
        faces_extraction_queue_url="https://sqs.local/face-extraction",
        rekognition_client=FakeRekognitionClient(face_details=faces, fail=rek_fail),
        s3_client=FakeS3Client(),
        sqs_client=FakeSqsClient(),
        ms4_client=FakeMs4Client(status=ms4_status),
    )


def test_process_record_success_with_faces_enqueues_ms3_job():
    service = make_service(faces=[{"BoundingBox": {"Width": 0.2}}])

    result = service.process_sqs_record(body=_s3_event_body(), message_id="msg-1")

    assert result["processed"] == 1
    assert len(service._ms4.calls) == 2
    assert service._ms4.calls[0][1]["eventType"] == "detection_started"
    assert service._ms4.calls[1][1]["eventType"] == "detection_completed"
    assert len(service._s3.put_calls) == 1
    artifact_payload = json.loads(service._s3.put_calls[0]["Body"].decode("utf-8"))
    assert artifact_payload["sourceKey"] == "processed/faces/s-1/upl-1.jpg"
    assert len(service._s3.copy_calls) == 1
    assert service._s3.copy_calls[0]["Key"] == "processed/faces/s-1/upl-1.jpg"
    assert len(service._s3.delete_calls) == 1
    assert service._s3.delete_calls[0]["Key"] == "uploaded/s-1/upl-1.jpg"
    assert service._ms4.calls[1][1]["details"]["sourceKey"] == "processed/faces/s-1/upl-1.jpg"
    assert len(service._sqs.messages) == 1
    msg_body = json.loads(service._sqs.messages[0]["MessageBody"])
    assert msg_body["contractVersion"] == "faces-extraction.v1"
    assert msg_body["sourceKey"] == "processed/faces/s-1/upl-1.jpg"


def test_process_record_with_no_faces_marks_failed_and_no_enqueue():
    service = make_service(faces=[])

    result = service.process_sqs_record(body=_s3_event_body(), message_id="msg-2")

    assert result["processed"] == 1
    assert len(service._ms4.calls) == 3
    assert service._ms4.calls[-1][1]["eventType"] == "detection_failed"
    assert service._ms4.calls[-1][1]["details"]["sourceKey"] == "processed/nofaces/s-1/upl-1.jpg"
    artifact_payload = json.loads(service._s3.put_calls[0]["Body"].decode("utf-8"))
    assert artifact_payload["sourceKey"] == "processed/nofaces/s-1/upl-1.jpg"
    assert len(service._s3.copy_calls) == 1
    assert service._s3.copy_calls[0]["Key"] == "processed/nofaces/s-1/upl-1.jpg"
    assert len(service._sqs.messages) == 0


def test_process_record_raises_retryable_error_for_rekognition_failure():
    service = make_service(rek_fail=True)

    with pytest.raises(DetectionError) as exc:
        service.process_sqs_record(body=_s3_event_body(), message_id="msg-3")
    assert exc.value.code == "DEPENDENCY_UNAVAILABLE"
    assert exc.value.retryable is True


def test_process_record_ignores_non_uploaded_prefix():
    service = make_service(faces=[{"BoundingBox": {"Width": 0.2}}])

    result = service.process_sqs_record(body=_s3_event_body(key="faces/s-1/upl-1.jpg"), message_id="msg-4")

    assert result["processed"] == 0
    assert result["ignored"] == 1

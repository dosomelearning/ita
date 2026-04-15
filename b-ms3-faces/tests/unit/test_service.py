from __future__ import annotations

import io
import json

import pytest
from botocore.exceptions import ClientError

from src.domain import ExtractionError
from src.service import FacesService


class FakeBody:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


class FakeS3Client:
    def __init__(self):
        self.put_calls: list[dict] = []
        self._objects: dict[tuple[str, str], bytes] = {}
        self.fail_put = False

    def set_object(self, *, bucket: str, key: str, body: bytes) -> None:
        self._objects[(bucket, key)] = body

    def get_object(self, *, Bucket: str, Key: str):
        content = self._objects.get((Bucket, Key))
        if content is None:
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "missing"}}, "GetObject")
        return {"Body": FakeBody(content)}

    def put_object(self, **kwargs):
        if self.fail_put:
            raise ClientError({"Error": {"Code": "ServiceUnavailable", "Message": "down"}}, "PutObject")
        self.put_calls.append(kwargs)
        body = kwargs["Body"]
        if isinstance(body, bytes):
            self._objects[(kwargs["Bucket"], kwargs["Key"])] = body


class FakeMs4Client:
    def __init__(self, *, status: int = 200):
        self.status = status
        self.calls: list[tuple[str, dict]] = []

    def post_event(self, *, upload_id: str, payload: dict):
        self.calls.append((upload_id, payload))
        return self.status, {"ok": self.status < 300}


def _job_body(event_time: str = "2026-04-16T08:00:00Z") -> str:
    return json.dumps(
        {
            "contractVersion": "faces-extraction.v1",
            "uploadId": "upl-1",
            "sessionId": "cr-1",
            "sourceBucket": "ita-data",
            "sourceKey": "processed/faces/cr-1/upl-1.jpg",
            "detectionArtifactKey": "rekognition/cr-1/upl-1.json",
            "detectedFaces": 2,
            "eventTime": event_time,
        }
    )


def _artifact_payload() -> bytes:
    return json.dumps(
        {
            "contractVersion": "rekognition-artifact.v1",
            "faces": [
                {"BoundingBox": {"Left": 0.1, "Top": 0.1, "Width": 0.2, "Height": 0.2}},
                {"BoundingBox": {"Left": 0.5, "Top": 0.3, "Width": 0.3, "Height": 0.3}},
            ],
        }
    ).encode("utf-8")


def make_service():
    s3 = FakeS3Client()
    ms4 = FakeMs4Client()
    service = FacesService(
        processing_bucket_name="ita-data",
        s3_client=s3,
        ms4_client=ms4,
    )
    return service, s3, ms4


def test_process_record_success_posts_completed_and_writes_faces(monkeypatch):
    service, s3, ms4 = make_service()
    s3.set_object(bucket="ita-data", key="rekognition/cr-1/upl-1.json", body=_artifact_payload())
    s3.set_object(bucket="ita-data", key="processed/faces/cr-1/upl-1.jpg", body=b"image-bytes")
    monkeypatch.setattr(
        "src.service._extract_faces_from_image",
        lambda source_bytes, face_boxes: [b"f1", b"f2"],  # noqa: ARG005
    )

    result = service.process_sqs_record(body=_job_body(), message_id="m-1")

    assert result["processed"] == 1
    assert len(s3.put_calls) == 2
    assert s3.put_calls[0]["Key"] == "faces/cr-1/upl-1/face-001.jpg"
    assert len(ms4.calls) == 1
    assert ms4.calls[0][1]["eventType"] == "extraction_completed"
    assert ms4.calls[0][1]["details"]["results"]["faceCount"] == 2
    assert ms4.calls[0][1]["eventTime"] == "2026-04-16T08:00:00.000Z"


def test_process_record_non_retryable_posts_failed_and_continues(monkeypatch):
    service, s3, ms4 = make_service()
    s3.set_object(bucket="ita-data", key="rekognition/cr-1/upl-1.json", body=_artifact_payload())
    s3.set_object(bucket="ita-data", key="processed/faces/cr-1/upl-1.jpg", body=b"image-bytes")
    monkeypatch.setattr(
        "src.service._extract_faces_from_image",
        lambda source_bytes, face_boxes: [],  # noqa: ARG005
    )

    result = service.process_sqs_record(body=_job_body(), message_id="m-2")

    assert result["processed"] == 1
    assert result["failed"] is True
    assert len(ms4.calls) == 1
    assert ms4.calls[0][1]["eventType"] == "extraction_failed"


def test_process_record_retryable_put_failure_raises(monkeypatch):
    service, s3, _ = make_service()
    s3.set_object(bucket="ita-data", key="rekognition/cr-1/upl-1.json", body=_artifact_payload())
    s3.set_object(bucket="ita-data", key="processed/faces/cr-1/upl-1.jpg", body=b"image-bytes")
    s3.fail_put = True
    monkeypatch.setattr(
        "src.service._extract_faces_from_image",
        lambda source_bytes, face_boxes: [b"f1"],  # noqa: ARG005
    )

    with pytest.raises(ExtractionError) as exc:
        service.process_sqs_record(body=_job_body(), message_id="m-3")
    assert exc.value.code == "DEPENDENCY_UNAVAILABLE"


def test_extract_faces_from_image_helper_when_pillow_available():
    pil = pytest.importorskip("PIL.Image")
    from src.service import _extract_faces_from_image

    image = pil.new("RGB", (100, 100), color=(255, 255, 255))
    out = io.BytesIO()
    image.save(out, format="JPEG")
    source_bytes = out.getvalue()

    faces = _extract_faces_from_image(
        source_bytes=source_bytes,
        face_boxes=[{"Left": 0.1, "Top": 0.1, "Width": 0.5, "Height": 0.5}],
    )
    assert len(faces) == 1
    assert isinstance(faces[0], bytes)

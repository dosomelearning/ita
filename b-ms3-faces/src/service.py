from __future__ import annotations

import io
import json
import logging
from typing import Any, Protocol

from botocore.exceptions import BotoCoreError, ClientError

try:  # Lambda runtime imports
    from domain import ExtractionError, ExtractionJob, parse_extraction_job
except ImportError:  # Unit tests/package imports
    from .domain import ExtractionError, ExtractionJob, parse_extraction_job

LOGGER = logging.getLogger(__name__)


class Ms4EventClient(Protocol):
    def post_event(self, *, upload_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
        ...


class FacesService:
    def __init__(
        self,
        *,
        processing_bucket_name: str,
        s3_client: Any,
        ms4_client: Ms4EventClient,
    ) -> None:
        self._processing_bucket_name = processing_bucket_name
        self._s3 = s3_client
        self._ms4 = ms4_client

    def process_sqs_record(self, *, body: str, message_id: str) -> dict[str, Any]:
        job = parse_extraction_job(body)
        try:
            faces = self._extract_and_store_faces(job)
            self._post_ms4_event(
                upload_id=job.upload_id,
                payload={
                    "eventType": "extraction_completed",
                    "eventTime": job.event_time,
                    "producer": "ms3",
                    "statusAfter": "completed",
                    "details": {
                        "progress": {"stage": "completed"},
                        "sourceKey": job.source_key,
                        "detectionArtifactKey": job.detection_artifact_key,
                        "results": {
                            "faceCount": len(faces),
                            "faces": faces,
                        },
                    },
                },
            )
            return {"processed": 1, "messageId": message_id}
        except ExtractionError as exc:
            self._send_failed_state(job=job, error=exc)
            if exc.retryable:
                raise
            LOGGER.warning(
                "Non-retriable MS3 error",
                extra={
                    "messageId": message_id,
                    "code": exc.code,
                    "uploadId": exc.upload_id,
                    "sessionId": exc.session_id,
                    "details": exc.details,
                },
            )
            return {"processed": 1, "messageId": message_id, "failed": True}

    def _extract_and_store_faces(self, job: ExtractionJob) -> list[dict[str, Any]]:
        artifact = self._read_detection_artifact(job)
        face_boxes = _extract_bounding_boxes(artifact)
        if not face_boxes:
            raise ExtractionError(
                code="NO_DETECTION_BOXES",
                message="Detection artifact does not contain face boxes.",
                retryable=False,
                upload_id=job.upload_id,
                session_id=job.session_id,
                details={"detectionArtifactKey": job.detection_artifact_key},
            )

        source_bytes = self._read_source_bytes(job)
        crops = _extract_faces_from_image(source_bytes=source_bytes, face_boxes=face_boxes)
        if not crops:
            raise ExtractionError(
                code="EXTRACTION_EMPTY",
                message="No face crops produced from detection artifact.",
                retryable=False,
                upload_id=job.upload_id,
                session_id=job.session_id,
                details={"sourceKey": job.source_key},
            )

        results: list[dict[str, Any]] = []
        for idx, face_bytes in enumerate(crops, start=1):
            face_id = f"face-{idx:03d}"
            face_key = f"faces/{job.session_id}/{job.upload_id}/{face_id}.jpg"
            try:
                self._s3.put_object(
                    Bucket=self._processing_bucket_name,
                    Key=face_key,
                    Body=face_bytes,
                    ContentType="image/jpeg",
                )
            except (ClientError, BotoCoreError) as exc:
                raise ExtractionError(
                    code="DEPENDENCY_UNAVAILABLE",
                    message="Unable to write extracted face image.",
                    retryable=True,
                    upload_id=job.upload_id,
                    session_id=job.session_id,
                    details={"dependency": "s3", "faceKey": face_key},
                ) from exc
            results.append(
                {
                    "faceId": face_id,
                    "bucket": self._processing_bucket_name,
                    "key": face_key,
                }
            )
        return results

    def _read_detection_artifact(self, job: ExtractionJob) -> dict[str, Any]:
        try:
            response = self._s3.get_object(
                Bucket=self._processing_bucket_name,
                Key=job.detection_artifact_key,
            )
        except (ClientError, BotoCoreError) as exc:
            raise ExtractionError(
                code="DEPENDENCY_UNAVAILABLE",
                message="Unable to read detection artifact.",
                retryable=True,
                upload_id=job.upload_id,
                session_id=job.session_id,
                details={"dependency": "s3", "detectionArtifactKey": job.detection_artifact_key},
            ) from exc
        body = response.get("Body")
        if body is None:
            raise ExtractionError(
                code="INVALID_ARTIFACT",
                message="Detection artifact body is missing.",
                retryable=False,
                upload_id=job.upload_id,
                session_id=job.session_id,
                details={"detectionArtifactKey": job.detection_artifact_key},
            )
        raw = body.read()
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExtractionError(
                code="INVALID_ARTIFACT",
                message="Detection artifact is not valid JSON.",
                retryable=False,
                upload_id=job.upload_id,
                session_id=job.session_id,
                details={"detectionArtifactKey": job.detection_artifact_key},
            ) from exc
        if not isinstance(parsed, dict):
            raise ExtractionError(
                code="INVALID_ARTIFACT",
                message="Detection artifact must be a JSON object.",
                retryable=False,
                upload_id=job.upload_id,
                session_id=job.session_id,
            )
        return parsed

    def _read_source_bytes(self, job: ExtractionJob) -> bytes:
        try:
            response = self._s3.get_object(Bucket=job.source_bucket, Key=job.source_key)
        except (ClientError, BotoCoreError) as exc:
            raise ExtractionError(
                code="DEPENDENCY_UNAVAILABLE",
                message="Unable to read source image.",
                retryable=True,
                upload_id=job.upload_id,
                session_id=job.session_id,
                details={"dependency": "s3", "sourceBucket": job.source_bucket, "sourceKey": job.source_key},
            ) from exc
        body = response.get("Body")
        if body is None:
            raise ExtractionError(
                code="INVALID_SOURCE_IMAGE",
                message="Source image body is missing.",
                retryable=False,
                upload_id=job.upload_id,
                session_id=job.session_id,
                details={"sourceKey": job.source_key},
            )
        content = body.read()
        if not content:
            raise ExtractionError(
                code="INVALID_SOURCE_IMAGE",
                message="Source image is empty.",
                retryable=False,
                upload_id=job.upload_id,
                session_id=job.session_id,
                details={"sourceKey": job.source_key},
            )
        return content

    def _post_ms4_event(self, *, upload_id: str, payload: dict[str, Any]) -> None:
        status, response_payload = self._ms4.post_event(upload_id=upload_id, payload=payload)
        if 200 <= status < 300:
            return
        details: dict[str, Any] = {"dependency": "ms4", "statusCode": status}
        if isinstance(response_payload, dict):
            details["response"] = response_payload
        raise ExtractionError(
            code="DEPENDENCY_UNAVAILABLE",
            message="MS4 event write failed.",
            retryable=True,
            upload_id=upload_id,
            details=details,
        )

    def _send_failed_state(self, *, job: ExtractionJob, error: ExtractionError) -> None:
        payload = {
            "eventType": "extraction_failed",
            "eventTime": job.event_time,
            "producer": "ms3",
            "statusAfter": "failed",
            "details": {
                "progress": {"stage": "failed"},
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "retryable": error.retryable,
                    "details": error.details,
                },
            },
        }
        try:
            self._post_ms4_event(upload_id=job.upload_id, payload=payload)
        except ExtractionError:
            LOGGER.warning("Unable to post MS4 failed state", extra={"uploadId": job.upload_id})


def _extract_bounding_boxes(artifact: dict[str, Any]) -> list[dict[str, float]]:
    raw_faces = artifact.get("faces")
    if not isinstance(raw_faces, list):
        return []
    face_boxes: list[dict[str, float]] = []
    for face in raw_faces:
        if not isinstance(face, dict):
            continue
        box = face.get("BoundingBox")
        if not isinstance(box, dict):
            continue
        left = _as_float(box.get("Left"))
        top = _as_float(box.get("Top"))
        width = _as_float(box.get("Width"))
        height = _as_float(box.get("Height"))
        if None in (left, top, width, height):
            continue
        if width <= 0 or height <= 0:
            continue
        face_boxes.append(
            {
                "Left": left,
                "Top": top,
                "Width": width,
                "Height": height,
            }
        )
    return face_boxes


def _extract_faces_from_image(*, source_bytes: bytes, face_boxes: list[dict[str, float]]) -> list[bytes]:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise ExtractionError(
            code="RUNTIME_DEPENDENCY_MISSING",
            message="Pillow dependency is required for image extraction.",
            retryable=False,
        ) from exc

    try:
        image = Image.open(io.BytesIO(source_bytes))
        image.load()
    except Exception as exc:  # pragma: no cover
        raise ExtractionError(
            code="INVALID_SOURCE_IMAGE",
            message="Unable to decode source image.",
            retryable=False,
        ) from exc

    width, height = image.size
    if width < 1 or height < 1:
        return []

    outputs: list[bytes] = []
    for box in face_boxes:
        left_px = max(0, min(width - 1, int(round(box["Left"] * width))))
        top_px = max(0, min(height - 1, int(round(box["Top"] * height))))
        right_px = max(left_px + 1, min(width, int(round((box["Left"] + box["Width"]) * width))))
        bottom_px = max(top_px + 1, min(height, int(round((box["Top"] + box["Height"]) * height))))
        cropped = image.crop((left_px, top_px, right_px, bottom_px)).convert("RGB")
        out = io.BytesIO()
        cropped.save(out, format="JPEG", quality=92)
        outputs.append(out.getvalue())
    return outputs


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None

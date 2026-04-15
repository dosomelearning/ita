from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from botocore.exceptions import BotoCoreError, ClientError

try:  # Lambda runtime imports
    from domain import DetectionError, UploadedObject, make_ms4_event, parse_sqs_body, parse_uploaded_object, utc_now_iso
except ImportError:  # Unit tests/package imports
    from .domain import DetectionError, UploadedObject, make_ms4_event, parse_sqs_body, parse_uploaded_object, utc_now_iso

LOGGER = logging.getLogger(__name__)


class Ms4EventClient(Protocol):
    def post_event(self, *, upload_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
        ...


class DetectionService:
    def __init__(
        self,
        *,
        processing_bucket_name: str,
        faces_extraction_queue_url: str,
        rekognition_client: Any,
        s3_client: Any,
        sqs_client: Any,
        ms4_client: Ms4EventClient,
    ) -> None:
        self._processing_bucket_name = processing_bucket_name
        self._faces_extraction_queue_url = faces_extraction_queue_url
        self._rekognition = rekognition_client
        self._s3 = s3_client
        self._sqs = sqs_client
        self._ms4 = ms4_client

    def process_sqs_record(self, *, body: str, message_id: str) -> dict[str, Any]:
        parsed_records = parse_sqs_body(body)
        processed = 0
        ignored = 0

        for item in parsed_records:
            try:
                uploaded = parse_uploaded_object(item)
                self._process_uploaded_object(uploaded)
                processed += 1
            except DetectionError as exc:
                if exc.code == "IGNORED_PREFIX":
                    ignored += 1
                    LOGGER.info("Skipping non-uploaded object key", extra={"messageId": message_id, "details": exc.details})
                    continue

                if not exc.retryable and exc.upload_id:
                    self._send_failed_state(exc)
                if exc.retryable:
                    raise
                LOGGER.warning(
                    "Non-retriable MS2 error",
                    extra={
                        "messageId": message_id,
                        "code": exc.code,
                        "uploadId": exc.upload_id,
                        "sessionId": exc.session_id,
                        "details": exc.details,
                    },
                )
                continue

        return {"processed": processed, "ignored": ignored, "records": len(parsed_records)}

    def _process_uploaded_object(self, uploaded: UploadedObject) -> None:
        self._post_ms4_event(
            upload_id=uploaded.upload_id,
            payload=make_ms4_event(
                event_type="detection_started",
                status_after="processing",
                details={
                    "progress": {"stage": "detection_started"},
                    "sessionId": uploaded.session_id,
                    "sourceKey": uploaded.key,
                },
            ),
        )

        faces = self._detect_faces(uploaded)
        face_count = len(faces)
        processed_key = self._move_source_to_processed(uploaded=uploaded, detected_faces=face_count)
        processed_uploaded = UploadedObject(
            bucket=uploaded.bucket,
            key=processed_key,
            session_id=uploaded.session_id,
            upload_id=uploaded.upload_id,
        )
        artifact_key = self._store_detection_artifact(uploaded=processed_uploaded, faces=faces)

        self._post_ms4_event(
            upload_id=uploaded.upload_id,
            payload=make_ms4_event(
                event_type="detection_completed",
                status_after="processing",
                details={
                    "progress": {"stage": "detection_completed"},
                    "sessionId": uploaded.session_id,
                    "sourceBucket": processed_uploaded.bucket,
                    "sourceKey": processed_uploaded.key,
                    "detectionArtifactKey": artifact_key,
                    "detectedFaces": face_count,
                },
            ),
        )

        if face_count == 0:
            self._post_ms4_event(
                upload_id=uploaded.upload_id,
                payload=make_ms4_event(
                    event_type="detection_failed",
                    status_after="failed",
                    details={
                        "progress": {"stage": "failed"},
                        "error": {
                            "code": "NO_FACES_DETECTED",
                            "message": "No faces detected in uploaded image.",
                            "retryable": False,
                        },
                        "sourceKey": processed_uploaded.key,
                    },
                ),
            )
            return

        self._publish_extraction_job(
            uploaded=processed_uploaded,
            detection_artifact_key=artifact_key,
            detected_faces=face_count,
        )

    def _move_source_to_processed(self, *, uploaded: UploadedObject, detected_faces: int) -> str:
        destination_key = _build_processed_key(
            source_key=uploaded.key,
            session_id=uploaded.session_id,
            upload_id=uploaded.upload_id,
            has_faces=detected_faces > 0,
        )
        try:
            self._s3.copy_object(
                Bucket=self._processing_bucket_name,
                Key=destination_key,
                CopySource={"Bucket": uploaded.bucket, "Key": uploaded.key},
            )
            self._s3.delete_object(Bucket=uploaded.bucket, Key=uploaded.key)
        except (ClientError, BotoCoreError) as exc:
            raise DetectionError(
                code="DEPENDENCY_UNAVAILABLE",
                message="Unable to move processed source object.",
                retryable=True,
                upload_id=uploaded.upload_id,
                session_id=uploaded.session_id,
                details={
                    "dependency": "s3",
                    "sourceKey": uploaded.key,
                    "destinationKey": destination_key,
                },
            ) from exc
        return destination_key

    def _detect_faces(self, uploaded: UploadedObject) -> list[dict[str, Any]]:
        try:
            response = self._rekognition.detect_faces(
                Image={"S3Object": {"Bucket": uploaded.bucket, "Name": uploaded.key}},
                Attributes=["DEFAULT"],
            )
        except (ClientError, BotoCoreError) as exc:
            raise DetectionError(
                code="DEPENDENCY_UNAVAILABLE",
                message="Rekognition detect-faces call failed.",
                retryable=True,
                upload_id=uploaded.upload_id,
                session_id=uploaded.session_id,
                details={"dependency": "rekognition"},
            ) from exc
        details = response.get("FaceDetails")
        if not isinstance(details, list):
            return []
        return [item for item in details if isinstance(item, dict)]

    def _store_detection_artifact(self, *, uploaded: UploadedObject, faces: list[dict[str, Any]]) -> str:
        artifact_key = f"rekognition/{uploaded.session_id}/{uploaded.upload_id}.json"
        payload = {
            "contractVersion": "rekognition-artifact.v1",
            "uploadId": uploaded.upload_id,
            "sessionId": uploaded.session_id,
            "sourceBucket": uploaded.bucket,
            "sourceKey": uploaded.key,
            "detectedFaces": len(faces),
            "faces": faces,
            "generatedAt": utc_now_iso(),
            "producer": "ms2",
        }
        try:
            self._s3.put_object(
                Bucket=self._processing_bucket_name,
                Key=artifact_key,
                Body=json.dumps(payload).encode("utf-8"),
                ContentType="application/json",
            )
        except (ClientError, BotoCoreError) as exc:
            raise DetectionError(
                code="DEPENDENCY_UNAVAILABLE",
                message="Unable to write detection artifact.",
                retryable=True,
                upload_id=uploaded.upload_id,
                session_id=uploaded.session_id,
                details={"dependency": "s3", "artifactKey": artifact_key},
            ) from exc
        return artifact_key

    def _publish_extraction_job(self, *, uploaded: UploadedObject, detection_artifact_key: str, detected_faces: int) -> None:
        body = {
            "contractVersion": "faces-extraction.v1",
            "uploadId": uploaded.upload_id,
            "sessionId": uploaded.session_id,
            "sourceBucket": uploaded.bucket,
            "sourceKey": uploaded.key,
            "detectionArtifactKey": detection_artifact_key,
            "detectedFaces": detected_faces,
            "eventTime": utc_now_iso(),
            "trace": {"producer": "ms2"},
        }
        try:
            self._sqs.send_message(
                QueueUrl=self._faces_extraction_queue_url,
                MessageBody=json.dumps(body),
            )
        except (ClientError, BotoCoreError) as exc:
            raise DetectionError(
                code="DEPENDENCY_UNAVAILABLE",
                message="Unable to publish extraction job.",
                retryable=True,
                upload_id=uploaded.upload_id,
                session_id=uploaded.session_id,
                details={"dependency": "sqs", "queueUrl": self._faces_extraction_queue_url},
            ) from exc

    def _post_ms4_event(self, *, upload_id: str, payload: dict[str, Any]) -> None:
        status, response_payload = self._ms4.post_event(upload_id=upload_id, payload=payload)
        if 200 <= status < 300:
            return
        details: dict[str, Any] = {"dependency": "ms4", "statusCode": status}
        if isinstance(response_payload, dict):
            details["response"] = response_payload
        raise DetectionError(
            code="DEPENDENCY_UNAVAILABLE",
            message="MS4 event write failed.",
            retryable=True,
            upload_id=upload_id,
            details=details,
        )

    def _send_failed_state(self, exc: DetectionError) -> None:
        assert exc.upload_id is not None
        details = {
            "progress": {"stage": "failed"},
            "error": {
                "code": exc.code,
                "message": exc.message,
                "retryable": exc.retryable,
            },
        }
        if exc.details:
            details["error"]["details"] = exc.details

        payload = make_ms4_event(
            event_type="detection_failed",
            status_after="failed",
            details=details,
        )
        try:
            self._post_ms4_event(upload_id=exc.upload_id, payload=payload)
        except DetectionError:
            LOGGER.warning("Unable to post MS4 failed state for non-retriable error", extra={"uploadId": exc.upload_id})


def _build_processed_key(*, source_key: str, session_id: str, upload_id: str, has_faces: bool) -> str:
    file_name = source_key.rsplit("/", 1)[-1]
    extension = ""
    if "." in file_name:
        extension = "." + file_name.rsplit(".", 1)[-1]
    suffix = "faces" if has_faces else "nofaces"
    return f"processed/{suffix}/{session_id}/{upload_id}{extension}"

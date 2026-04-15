from __future__ import annotations

import hmac
import hashlib
import logging
import time
import uuid
from typing import Any, Protocol

from botocore.exceptions import ClientError

try:  # Lambda runtime imports
    from domain import IngressError, UploadInitRequest, utc_now_iso, validate_upload_init_payload
except ImportError:  # Unit tests/package imports
    from .domain import IngressError, UploadInitRequest, utc_now_iso, validate_upload_init_payload


class Ms4RegistrationClient(Protocol):
    def register_upload_init(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
        ...

    def post_event(self, *, upload_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
        ...


class IngressService:
    def __init__(
        self,
        *,
        shared_password_parameter_name: str,
        processing_bucket_name: str,
        presign_expires_seconds: int,
        ssm_client: Any,
        s3_client: Any,
        ms4_client: Ms4RegistrationClient,
    ) -> None:
        self._shared_password_parameter_name = shared_password_parameter_name
        self._processing_bucket_name = processing_bucket_name
        self._presign_expires_seconds = presign_expires_seconds
        self._ssm_client = ssm_client
        self._s3_client = s3_client
        self._ms4_client = ms4_client

    def handle_upload_init(self, payload: dict[str, Any]) -> dict[str, Any]:
        started_at = time.perf_counter()
        request = validate_upload_init_payload(payload)

        ssm_started_at = time.perf_counter()
        stored_password = self._read_shared_password()
        ssm_duration_ms = _duration_ms(ssm_started_at)

        if not hmac.compare_digest(request.password, stored_password):
            _LOG.info(
                "upload_init rejected invalid_password ssm_ms=%d total_ms=%d",
                ssm_duration_ms,
                _duration_ms(started_at),
            )
            raise IngressError(
                code="INVALID_PASSWORD",
                message="Invalid class code. Ask instructor for current code.",
                status_code=401,
                retryable=False,
            )

        class_run_id = _build_class_run_id(request.password)
        upload_id = _new_upload_id()
        object_key = self._build_object_key(session_id=class_run_id, upload_id=upload_id)

        ms4_started_at = time.perf_counter()
        self._register_ms4_init(upload_id=upload_id, request=request, class_run_id=class_run_id)
        self._post_ms4_event(
            upload_id=upload_id,
            event_type="upload_init_received",
            details={
                "phase": "pending_upload",
                "uploadReady": False,
                "sessionId": class_run_id,
                "contentType": request.content_type,
            },
        )
        upload_url = self._create_presigned_url(object_key=object_key, content_type=request.content_type)
        self._post_ms4_event(
            upload_id=upload_id,
            event_type="upload_url_issued",
            details={
                "phase": "upload_ready",
                "uploadReady": True,
                "sessionId": class_run_id,
                "objectKey": object_key,
                "contentType": request.content_type,
            },
        )
        ms4_duration_ms = _duration_ms(ms4_started_at)

        _LOG.info(
            "upload_init accepted ssm_ms=%d ms4_ms=%d total_ms=%d",
            ssm_duration_ms,
            ms4_duration_ms,
            _duration_ms(started_at),
        )

        return {
            "accepted": True,
            "uploadId": upload_id,
            "classRunId": class_run_id,
            "uploadUrl": upload_url,
            "uploadMethod": "PUT",
            "uploadHeaders": {"Content-Type": request.content_type},
            "objectKey": object_key,
            "expiresInSeconds": self._presign_expires_seconds,
        }

    def _read_shared_password(self) -> str:
        try:
            response = self._ssm_client.get_parameter(
                Name=self._shared_password_parameter_name,
                WithDecryption=True,
            )
        except ClientError as exc:
            raise IngressError(
                code="DEPENDENCY_UNAVAILABLE",
                message="Unable to read shared password configuration.",
                status_code=503,
                retryable=True,
                details={"dependency": "ssm"},
            ) from exc

        value = response.get("Parameter", {}).get("Value")
        if not isinstance(value, str) or not value:
            raise IngressError(
                code="INTERNAL_ERROR",
                message="Shared password configuration is empty.",
                status_code=500,
                retryable=False,
                details={"dependency": "ssm"},
            )
        return value

    def _build_object_key(self, *, session_id: str, upload_id: str) -> str:
        return f"uploaded/{session_id}/{upload_id}.jpg"

    def _create_presigned_url(self, *, object_key: str, content_type: str) -> str:
        try:
            return self._s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self._processing_bucket_name,
                    "Key": object_key,
                    "ContentType": content_type,
                },
                ExpiresIn=self._presign_expires_seconds,
                HttpMethod="PUT",
            )
        except ClientError as exc:
            raise IngressError(
                code="DEPENDENCY_UNAVAILABLE",
                message="Unable to generate upload URL.",
                status_code=503,
                retryable=True,
                details={"dependency": "s3-presign"},
            ) from exc

    def _register_ms4_init(self, *, upload_id: str, request: UploadInitRequest, class_run_id: str) -> None:
        status, response_payload = self._ms4_client.register_upload_init(
            {
                "uploadId": upload_id,
                "sessionId": class_run_id,
                "submittedAt": utc_now_iso(),
                "source": "spa",
                "nickname": request.nickname,
            }
        )
        if 200 <= status < 300:
            return
        message = "Unable to register upload state in MS4."
        if isinstance(response_payload, dict):
            error = response_payload.get("error")
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                message = error["message"]
        raise IngressError(
            code="DEPENDENCY_UNAVAILABLE",
            message=message,
            status_code=503,
            retryable=True,
            details={"dependency": "ms4", "statusCode": status},
        )

    def _post_ms4_event(self, *, upload_id: str, event_type: str, details: dict[str, Any]) -> None:
        status, response_payload = self._ms4_client.post_event(
            upload_id=upload_id,
            payload={
                "eventType": event_type,
                "eventTime": utc_now_iso(),
                "producer": "ms1",
                "statusAfter": "queued",
                "details": details,
            },
        )
        if 200 <= status < 300:
            return
        message = "Unable to register upload event in MS4."
        if isinstance(response_payload, dict):
            error = response_payload.get("error")
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                message = error["message"]
        raise IngressError(
            code="DEPENDENCY_UNAVAILABLE",
            message=message,
            status_code=503,
            retryable=True,
            details={"dependency": "ms4", "statusCode": status, "eventType": event_type},
        )


def _new_upload_id() -> str:
    return f"upl-{uuid.uuid4().hex[:16]}"


def _build_class_run_id(class_code: str) -> str:
    digest = hashlib.sha256(class_code.strip().encode("utf-8")).hexdigest()[:16]
    return f"cr-{digest}"


def _duration_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


_LOG = logging.getLogger(__name__)

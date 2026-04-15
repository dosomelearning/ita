from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import unquote_plus


class DetectionError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        retryable: bool,
        details: dict[str, Any] | None = None,
        upload_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}
        self.upload_id = upload_id
        self.session_id = session_id


@dataclass(frozen=True)
class UploadedObject:
    bucket: str
    key: str
    session_id: str
    upload_id: str


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_sqs_body(body: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DetectionError(
            code="INVALID_MESSAGE",
            message="SQS message body must be valid JSON.",
            retryable=False,
        ) from exc
    records = parsed.get("Records")
    if not isinstance(records, list) or not records:
        raise DetectionError(
            code="INVALID_MESSAGE",
            message="SQS message body must include non-empty Records list.",
            retryable=False,
        )
    return records


def parse_uploaded_object(record: dict[str, Any]) -> UploadedObject:
    event_source = record.get("eventSource")
    event_name = record.get("eventName")
    if event_source != "aws:s3" or not isinstance(event_name, str) or not event_name.startswith("ObjectCreated"):
        raise DetectionError(
            code="UNSUPPORTED_EVENT",
            message="Unsupported event source or event name for MS2.",
            retryable=False,
            details={"eventSource": event_source, "eventName": event_name},
        )

    s3 = record.get("s3")
    if not isinstance(s3, dict):
        raise DetectionError(
            code="INVALID_MESSAGE",
            message="Missing s3 payload.",
            retryable=False,
        )
    bucket = ((s3.get("bucket") or {}).get("name")) if isinstance(s3.get("bucket"), dict) else None
    key_raw = ((s3.get("object") or {}).get("key")) if isinstance(s3.get("object"), dict) else None
    if not isinstance(bucket, str) or not bucket.strip() or not isinstance(key_raw, str) or not key_raw.strip():
        raise DetectionError(
            code="INVALID_MESSAGE",
            message="S3 bucket name and object key are required.",
            retryable=False,
        )

    key = unquote_plus(key_raw)
    if not key.startswith("uploaded/"):
        raise DetectionError(
            code="IGNORED_PREFIX",
            message="Object key is outside uploaded/ prefix.",
            retryable=False,
            details={"key": key},
        )

    parts = key.split("/")
    if len(parts) < 3:
        raise DetectionError(
            code="INVALID_KEY_FORMAT",
            message="Uploaded object key must be uploaded/{sessionId}/{uploadId}.<ext>.",
            retryable=False,
            details={"key": key},
        )

    session_id = parts[1].strip()
    file_name = parts[-1].strip()
    upload_id = file_name.split(".", 1)[0].strip()
    if not session_id or not upload_id:
        raise DetectionError(
            code="INVALID_KEY_FORMAT",
            message="Object key does not contain sessionId/uploadId.",
            retryable=False,
            details={"key": key},
        )

    return UploadedObject(bucket=bucket.strip(), key=key, session_id=session_id, upload_id=upload_id)


def make_ms4_event(
    *,
    event_type: str,
    status_after: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "eventType": event_type,
        "eventTime": utc_now_iso(),
        "producer": "ms2",
        "statusAfter": status_after,
        "details": details,
    }

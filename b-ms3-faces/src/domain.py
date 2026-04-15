from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


class ExtractionError(Exception):
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
class ExtractionJob:
    upload_id: str
    session_id: str
    source_bucket: str
    source_key: str
    detection_artifact_key: str
    detected_faces: int
    event_time: str


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_extraction_job(body: str) -> ExtractionJob:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ExtractionError(
            code="INVALID_MESSAGE",
            message="SQS message body must be valid JSON.",
            retryable=False,
        ) from exc
    if not isinstance(payload, dict):
        raise ExtractionError(
            code="INVALID_MESSAGE",
            message="SQS message body must be a JSON object.",
            retryable=False,
        )

    contract_version = _required_string(payload, "contractVersion")
    if contract_version != "faces-extraction.v1":
        raise ExtractionError(
            code="UNSUPPORTED_CONTRACT",
            message="Unsupported extraction contract version.",
            retryable=False,
            details={"contractVersion": contract_version},
            upload_id=_optional_string(payload.get("uploadId")),
            session_id=_optional_string(payload.get("sessionId")),
        )

    upload_id = _required_string(payload, "uploadId")
    session_id = _required_string(payload, "sessionId")
    source_bucket = _required_string(payload, "sourceBucket")
    source_key = _required_string(payload, "sourceKey")
    detection_artifact_key = _required_string(payload, "detectionArtifactKey")
    detected_faces = _required_int(payload, "detectedFaces", minimum=1)
    event_time = parse_iso8601(_required_string(payload, "eventTime"))
    return ExtractionJob(
        upload_id=upload_id,
        session_id=session_id,
        source_bucket=source_bucket,
        source_key=source_key,
        detection_artifact_key=detection_artifact_key,
        detected_faces=detected_faces,
        event_time=event_time,
    )


def parse_iso8601(value: str) -> str:
    raw = value.strip()
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ExtractionError(
            code="INVALID_MESSAGE",
            message="eventTime must be valid ISO 8601.",
            retryable=False,
            details={"eventTime": value},
        ) from exc
    return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ExtractionError(
            code="INVALID_MESSAGE",
            message=f"{field} is required and must be a non-empty string.",
            retryable=False,
            details={"field": field},
        )
    return value.strip()


def _required_int(payload: dict[str, Any], field: str, *, minimum: int = 0) -> int:
    value = payload.get(field)
    if not isinstance(value, int) or value < minimum:
        raise ExtractionError(
            code="INVALID_MESSAGE",
            message=f"{field} must be an integer >= {minimum}.",
            retryable=False,
            details={"field": field, "value": value},
        )
    return value


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None

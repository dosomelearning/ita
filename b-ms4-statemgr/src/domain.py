from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

ALLOWED_STATES = {"queued", "processing", "completed", "failed"}


class DomainError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}


@dataclass(frozen=True)
class InitRequest:
    upload_id: str
    session_id: str
    nickname: str
    participant_id: str
    submitted_at: str
    source: str


@dataclass(frozen=True)
class EventRequest:
    upload_id: str
    event_type: str
    event_time: str
    producer: str
    status_after: str
    details: dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_iso8601(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError(
            code="VALIDATION_ERROR",
            message="Timestamp must be a non-empty string.",
            status_code=400,
            details={"field": "timestamp"},
        )
    raw = value.strip()
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DomainError(
            code="VALIDATION_ERROR",
            message="Timestamp must be valid ISO 8601.",
            status_code=400,
            details={"value": value},
        ) from exc
    return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def validate_init_payload(payload: dict[str, Any]) -> InitRequest:
    upload_id = _required_string(payload, "uploadId")
    session_id = _required_string(payload, "sessionId")
    nickname = _required_string(payload, "nickname")
    submitted_at = parse_iso8601(_required_string(payload, "submittedAt"))
    source = _required_string(payload, "source")
    if source != "spa":
        raise DomainError(
            code="VALIDATION_ERROR",
            message="source must be 'spa' for current contract.",
            status_code=400,
            details={"source": source},
        )
    return InitRequest(
        upload_id=upload_id,
        session_id=session_id,
        nickname=nickname,
        participant_id=build_participant_id(nickname),
        submitted_at=submitted_at,
        source=source,
    )


def validate_event_payload(upload_id: str, payload: dict[str, Any]) -> EventRequest:
    event_type = _required_string(payload, "eventType")
    event_time = parse_iso8601(_required_string(payload, "eventTime"))
    producer = _required_string(payload, "producer")
    status_after = _required_string(payload, "statusAfter")
    details = payload.get("details", {})
    if not isinstance(details, dict):
        raise DomainError(
            code="VALIDATION_ERROR",
            message="details must be an object when present.",
            status_code=400,
            details={"field": "details"},
        )
    if producer not in {"ms1", "ms2", "ms3"}:
        raise DomainError(
            code="VALIDATION_ERROR",
            message="producer must be one of: ms1, ms2, ms3.",
            status_code=400,
            details={"producer": producer},
        )
    if status_after not in ALLOWED_STATES:
        raise DomainError(
            code="VALIDATION_ERROR",
            message="statusAfter is invalid.",
            status_code=400,
            details={"statusAfter": status_after},
        )
    allowed_by_producer = {
        "ms1": {"queued"},
        "ms2": {"queued", "processing", "failed"},
        "ms3": {"completed", "failed"},
    }[producer]
    if status_after not in allowed_by_producer:
        raise DomainError(
            code="VALIDATION_ERROR",
            message="statusAfter not allowed for producer.",
            status_code=400,
            details={"producer": producer, "statusAfter": status_after},
        )
    return EventRequest(
        upload_id=upload_id,
        event_type=event_type,
        event_time=event_time,
        producer=producer,
        status_after=status_after,
        details=details,
    )


def assert_transition_allowed(current_status: str, next_status: str) -> None:
    if current_status not in ALLOWED_STATES:
        raise DomainError(
            code="INTERNAL_ERROR",
            message="Current status is invalid in stored state.",
            status_code=500,
            retryable=False,
            details={"currentStatus": current_status},
        )
    allowed_map = {
        "queued": {"queued", "processing", "failed"},
        "processing": {"processing", "completed", "failed"},
        "completed": set(),
        "failed": set(),
    }
    if next_status not in allowed_map[current_status]:
        raise DomainError(
            code="INVALID_TRANSITION",
            message=f"State transition is not allowed from {current_status} to {next_status}.",
            status_code=409,
            retryable=False,
            details={"fromStatus": current_status, "toStatus": next_status},
        )


def build_event_sk(event_time: str, event_type: str, producer: str) -> str:
    return f"EVENT#{event_time}#{event_type}#{producer}"


def build_activity_gsi3pk(session_id: str) -> str:
    return f"FEED#CLASS#{session_id}"


def build_activity_gsi3sk(event_time: str, upload_id: str, event_type: str) -> str:
    return f"E#{event_time}#U#{upload_id}#T#{event_type}"


def build_participant_id(nickname: str) -> str:
    normalized = " ".join(nickname.strip().lower().split())
    if not normalized:
        raise DomainError(
            code="VALIDATION_ERROR",
            message="nickname is required and must be a non-empty string.",
            status_code=400,
            details={"field": "nickname"},
        )
    return normalized


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DomainError(
            code="VALIDATION_ERROR",
            message=f"{field} is required and must be a non-empty string.",
            status_code=400,
            details={"field": field},
        )
    return value.strip()

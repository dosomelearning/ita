from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
CLASS_CODE_PATTERN = re.compile(r"^\S+$")
NICKNAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,19}$")


class IngressError(Exception):
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
class UploadInitRequest:
    password: str
    nickname: str
    session_id: str
    content_type: str
    original_filename: str | None
    file_size_bytes: int | None


def validate_upload_init_payload(payload: dict[str, Any]) -> UploadInitRequest:
    password = _required_string(payload, "password")
    nickname = _required_string(payload, "nickname")
    session_id = _required_string(payload, "sessionId")
    _validate_class_code(password)
    _validate_nickname(nickname)
    content_type = _required_string(payload, "contentType").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise IngressError(
            code="VALIDATION_ERROR",
            message="contentType is not supported.",
            status_code=400,
            details={"allowedContentTypes": sorted(ALLOWED_CONTENT_TYPES)},
        )
    original_filename = payload.get("originalFilename")
    if original_filename is not None and (not isinstance(original_filename, str) or not original_filename.strip()):
        raise IngressError(
            code="VALIDATION_ERROR",
            message="originalFilename must be a non-empty string when present.",
            status_code=400,
            details={"field": "originalFilename"},
        )
    file_size_bytes = payload.get("fileSizeBytes")
    if file_size_bytes is not None:
        if not isinstance(file_size_bytes, int) or file_size_bytes < 1:
            raise IngressError(
                code="VALIDATION_ERROR",
                message="fileSizeBytes must be a positive integer when present.",
                status_code=400,
                details={"field": "fileSizeBytes"},
            )
    return UploadInitRequest(
        password=password,
        nickname=nickname,
        session_id=session_id,
        content_type=content_type,
        original_filename=original_filename.strip() if isinstance(original_filename, str) else None,
        file_size_bytes=file_size_bytes,
    )


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise IngressError(
            code="VALIDATION_ERROR",
            message=f"{field} is required and must be a non-empty string.",
            status_code=400,
            details={"field": field},
        )
    return value.strip()


def _validate_class_code(class_code: str) -> None:
    if not CLASS_CODE_PATTERN.fullmatch(class_code):
        raise IngressError(
            code="VALIDATION_ERROR",
            message="password must not contain spaces.",
            status_code=400,
            details={"field": "password"},
        )


def _validate_nickname(nickname: str) -> None:
    if not NICKNAME_PATTERN.fullmatch(nickname):
        raise IngressError(
            code="VALIDATION_ERROR",
            message="nickname must start with a letter and contain only letters/numbers (max 20, no spaces).",
            status_code=400,
            details={"field": "nickname"},
        )

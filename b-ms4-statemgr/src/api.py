from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import unquote

try:  # Lambda runtime import path
    from domain import DomainError, utc_now_iso
    from service import StateService
except ImportError:  # Unit tests/package import path
    from .domain import DomainError, utc_now_iso
    from .service import StateService

LOGGER = logging.getLogger(__name__)
UPLOAD_STATUS_PATH_RE = re.compile(r"^/v1/uploads/(?P<upload_id>[^/]+)/status$")
UPLOAD_EVENT_PATH_RE = re.compile(r"^/internal/uploads/(?P<upload_id>[^/]+)/events$")
PARTICIPANT_UPLOADS_PATH_RE = re.compile(
    r"^/v1/sessions/(?P<session_id>[^/]+)/participants/(?P<nickname>[^/]+)/uploads$"
)
SESSION_ACTIVITIES_PATH_RE = re.compile(r"^/v1/sessions/(?P<session_id>[^/]+)/activities$")


class Ms4Api:
    def __init__(self, service: StateService) -> None:
        self._service = service

    def handle(self, event: dict[str, Any], context: Any) -> dict[str, Any]:
        method = _get_method(event)
        path = _get_path(event)
        request_id = _get_request_id(event, context)
        principal = _get_principal(event)
        try:
            if method == "POST" and path == "/internal/uploads/init":
                payload = _json_body(event)
                result = self._service.register_upload_init(payload)
                return _ok(200, result)

            if method == "POST":
                match = UPLOAD_EVENT_PATH_RE.match(path)
                if match:
                    upload_id = match.group("upload_id")
                    payload = _json_body(event)
                    result = self._service.record_processing_event(upload_id, payload)
                    return _ok(200, result)

            if method == "GET":
                match = UPLOAD_STATUS_PATH_RE.match(path)
                if match:
                    upload_id = match.group("upload_id")
                    result = self._service.get_status(upload_id)
                    return _ok(200, result)
                match = PARTICIPANT_UPLOADS_PATH_RE.match(path)
                if match:
                    session_id = unquote(match.group("session_id"))
                    nickname = unquote(match.group("nickname"))
                    limit = _read_limit(event)
                    result = self._service.get_participant_uploads(
                        session_id=session_id,
                        nickname=nickname,
                        limit=limit,
                    )
                    return _ok(200, result)
                match = SESSION_ACTIVITIES_PATH_RE.match(path)
                if match:
                    session_id = unquote(match.group("session_id"))
                    limit = _read_limit(event)
                    result = self._service.get_session_activities(session_id=session_id, limit=limit)
                    return _ok(200, result)

            raise DomainError(
                code="NOT_FOUND",
                message="Route not found.",
                status_code=404,
                retryable=False,
                details={"method": method, "path": path},
            )
        except DomainError as exc:
            return _error_response(exc, request_id=request_id)
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("Unhandled MS4 error", extra={"requestId": request_id, "principal": principal})
            err = DomainError(
                code="INTERNAL_ERROR",
                message="Internal server error.",
                status_code=500,
                retryable=False,
                details={},
            )
            return _error_response(err, request_id=request_id)


def _get_method(event: dict[str, Any]) -> str:
    rc = event.get("requestContext", {})
    http = rc.get("http", {})
    return str(http.get("method") or event.get("httpMethod") or "").upper()


def _get_path(event: dict[str, Any]) -> str:
    return str(event.get("rawPath") or event.get("path") or "")


def _get_request_id(event: dict[str, Any], context: Any) -> str:
    rc = event.get("requestContext", {})
    request_id = rc.get("requestId")
    if isinstance(request_id, str) and request_id:
        return request_id
    context_id = getattr(context, "aws_request_id", None)
    if isinstance(context_id, str) and context_id:
        return context_id
    return "unknown-request-id"


def _get_principal(event: dict[str, Any]) -> str:
    rc = event.get("requestContext", {})
    authorizer = rc.get("authorizer", {})
    iam = authorizer.get("iam", {})
    user_arn = iam.get("userArn")
    if isinstance(user_arn, str) and user_arn:
        return user_arn
    return "anonymous"


def _json_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None:
        return {}
    if isinstance(body, str):
        if not body.strip():
            return {}
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise DomainError(
                code="VALIDATION_ERROR",
                message="Request body must be valid JSON.",
                status_code=400,
                retryable=False,
                details={"field": "body"},
            ) from exc
        if not isinstance(parsed, dict):
            raise DomainError(
                code="VALIDATION_ERROR",
                message="Request body must be a JSON object.",
                status_code=400,
                retryable=False,
                details={"field": "body"},
            )
        return parsed
    if isinstance(body, dict):
        return body
    raise DomainError(
        code="VALIDATION_ERROR",
        message="Unsupported request body type.",
        status_code=400,
        retryable=False,
        details={"field": "body"},
    )


def _ok(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _read_limit(event: dict[str, Any]) -> int:
    query = event.get("queryStringParameters")
    if not isinstance(query, dict):
        return 20
    raw_limit = query.get("limit")
    if raw_limit is None:
        return 20
    if not isinstance(raw_limit, str) or not raw_limit.strip():
        raise DomainError(
            code="VALIDATION_ERROR",
            message="limit must be a positive integer.",
            status_code=400,
            retryable=False,
            details={"field": "limit"},
        )
    try:
        parsed = int(raw_limit)
    except ValueError as exc:
        raise DomainError(
            code="VALIDATION_ERROR",
            message="limit must be a positive integer.",
            status_code=400,
            retryable=False,
            details={"field": "limit", "value": raw_limit},
        ) from exc
    if parsed < 1:
        raise DomainError(
            code="VALIDATION_ERROR",
            message="limit must be a positive integer.",
            status_code=400,
            retryable=False,
            details={"field": "limit", "value": raw_limit},
        )
    return parsed


def _error_response(err: DomainError, *, request_id: str) -> dict[str, Any]:
    payload = {
        "error": {
            "code": err.code,
            "message": err.message,
            "retryable": err.retryable,
            "details": err.details,
        },
        "requestId": request_id,
        "timestamp": utc_now_iso(),
    }
    return {
        "statusCode": err.status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }

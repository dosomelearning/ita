from __future__ import annotations

import json
from typing import Any

try:  # Lambda runtime imports
    from domain import IngressError, utc_now_iso
    from service import IngressService
except ImportError:  # Unit tests/package imports
    from .domain import IngressError, utc_now_iso
    from .service import IngressService


class IngressApi:
    def __init__(self, service: IngressService) -> None:
        self._service = service

    def handle(self, event: dict[str, Any], context: Any) -> dict[str, Any]:
        method = _http_method(event)
        path = _path(event)
        request_id = _request_id(event, context)
        try:
            if method == "POST" and path == "/v1/uploads/init":
                payload = _json_body(event)
                result = self._service.handle_upload_init(payload)
                return _ok(result, status_code=200)
            raise IngressError(
                code="NOT_FOUND",
                message="Route not found.",
                status_code=404,
                retryable=False,
                details={"method": method, "path": path},
            )
        except IngressError as exc:
            return _error(exc, request_id=request_id)
        except Exception:  # pragma: no cover
            return _error(
                IngressError(
                    code="INTERNAL_ERROR",
                    message="Internal server error.",
                    status_code=500,
                    retryable=False,
                ),
                request_id=request_id,
            )


def _http_method(event: dict[str, Any]) -> str:
    rc = event.get("requestContext", {})
    http = rc.get("http", {})
    return str(http.get("method") or event.get("httpMethod") or "").upper()


def _path(event: dict[str, Any]) -> str:
    return str(event.get("rawPath") or event.get("path") or "")


def _request_id(event: dict[str, Any], context: Any) -> str:
    rc = event.get("requestContext", {})
    rid = rc.get("requestId")
    if isinstance(rid, str) and rid:
        return rid
    context_rid = getattr(context, "aws_request_id", None)
    if isinstance(context_rid, str) and context_rid:
        return context_rid
    return "unknown-request-id"


def _json_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    if isinstance(body, str):
        if not body.strip():
            return {}
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise IngressError(
                code="VALIDATION_ERROR",
                message="Request body must be valid JSON.",
                status_code=400,
                details={"field": "body"},
            ) from exc
        if not isinstance(parsed, dict):
            raise IngressError(
                code="VALIDATION_ERROR",
                message="Request body must be a JSON object.",
                status_code=400,
                details={"field": "body"},
            )
        return parsed
    raise IngressError(
        code="VALIDATION_ERROR",
        message="Unsupported request body type.",
        status_code=400,
        details={"field": "body"},
    )


def _ok(payload: dict[str, Any], *, status_code: int) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _error(err: IngressError, *, request_id: str) -> dict[str, Any]:
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

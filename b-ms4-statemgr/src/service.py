from __future__ import annotations

from typing import Any

try:  # Lambda runtime import path
    from domain import (
        DomainError,
        EventRequest,
        InitRequest,
        assert_transition_allowed,
        build_activity_gsi3pk,
        build_activity_gsi3sk,
        build_event_sk,
        build_participant_id,
        utc_now_iso,
        validate_event_payload,
        validate_init_payload,
    )
    from repository import STATE_SK, StateRepository
except ImportError:  # Unit tests/package import path
    from .domain import (
        DomainError,
        EventRequest,
        InitRequest,
        assert_transition_allowed,
        build_activity_gsi3pk,
        build_activity_gsi3sk,
        build_event_sk,
        build_participant_id,
        utc_now_iso,
        validate_event_payload,
        validate_init_payload,
    )
    from .repository import STATE_SK, StateRepository


class StateService:
    def __init__(self, repository: StateRepository, *, cloudfront_domain: str = "") -> None:
        self._repository = repository
        self._cloudfront_domain = cloudfront_domain.strip()

    def register_upload_init(self, payload: dict[str, Any]) -> dict[str, Any]:
        req = validate_init_payload(payload)
        existing_state = self._repository.get_state(req.upload_id)
        if existing_state:
            if self._is_idempotent_init(existing_state, req):
                return self._to_status_response(existing_state)
            raise DomainError(
                code="TERMINAL_STATE_CONFLICT",
                message="Upload already exists with conflicting init payload.",
                status_code=409,
                retryable=False,
                details={"uploadId": req.upload_id},
            )

        now = utc_now_iso()
        state_item = {
            "PK": f"UPLOAD#{req.upload_id}",
            "SK": STATE_SK,
            "entityType": "STATE",
            "uploadId": req.upload_id,
            "sessionId": req.session_id,
            "nickname": req.nickname,
            "participantId": req.participant_id,
            "source": req.source,
            "status": "queued",
            "submittedAt": req.submitted_at,
            "updatedAt": now,
            "version": 1,
            "progress": {"stage": "queued"},
            "results": None,
            "error": None,
            "lastEventKey": "INIT",
            "gsi1pk": f"SESSION#{req.session_id}",
            "gsi1sk": f"UPDATED#{now}#UPLOAD#{req.upload_id}",
            "gsi2pk": f"PARTICIPANT#{req.session_id}#{req.participant_id}",
            "gsi2sk": f"SUBMITTED#{req.submitted_at}#UPLOAD#{req.upload_id}",
        }
        self._repository.create_initial_state(upload_id=req.upload_id, item=state_item)
        return self._to_status_response(state_item)

    def record_processing_event(self, upload_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = validate_event_payload(upload_id, payload)
        state = self._repository.get_state(upload_id)
        if not state:
            raise DomainError(
                code="UPLOAD_NOT_FOUND",
                message="Upload state not found.",
                status_code=404,
                details={"uploadId": upload_id},
            )

        event_sk = build_event_sk(req.event_time, req.event_type, req.producer)
        existing_event = self._repository.get_event(upload_id, event_sk)
        if existing_event:
            return self._to_status_response(state)

        current_status = str(state["status"])
        assert_transition_allowed(current_status, req.status_after)
        next_state = self._build_next_state(state=state, event=req, event_sk=event_sk)
        event_item = self._build_event_item(state=state, event=req, event_sk=event_sk)
        self._repository.apply_event_transition(
            upload_id=upload_id,
            prior_state=state,
            next_state=next_state,
            event_item=event_item,
        )
        return self._to_status_response(next_state)

    def get_status(self, upload_id: str) -> dict[str, Any]:
        state = self._repository.get_state(upload_id)
        if not state:
            raise DomainError(
                code="UPLOAD_NOT_FOUND",
                message="Upload state not found.",
                status_code=404,
                details={"uploadId": upload_id},
            )
        return self._to_status_response(state)

    def get_participant_uploads(self, *, session_id: str, nickname: str, limit: int = 20) -> dict[str, Any]:
        participant_id = build_participant_id(nickname)
        safe_limit = min(max(limit, 1), 50)
        items = self._repository.list_participant_states(
            session_id=session_id,
            participant_id=participant_id,
            limit=safe_limit,
        )
        return {
            "sessionId": session_id,
            "nickname": nickname,
            "participantId": participant_id,
            "items": [self._to_status_response(item) for item in items],
        }

    def get_session_activities(self, *, session_id: str, limit: int = 20) -> dict[str, Any]:
        safe_limit = min(max(limit, 1), 200)
        items = self._repository.list_session_activities(session_id=session_id, limit=safe_limit)
        activity_items = [
            {
                "uploadId": item.get("uploadId"),
                "sessionId": item.get("sessionId"),
                "nickname": item.get("nickname"),
                "participantId": item.get("participantId"),
                "eventType": item.get("eventType"),
                "statusAfter": item.get("statusAfter"),
                "eventTime": item.get("eventTime"),
                "producer": item.get("producer"),
                "outcome": _map_activity_outcome(str(item.get("statusAfter", ""))),
                "details": item.get("details", {}),
            }
            for item in items
        ]
        return {"sessionId": session_id, "items": activity_items}

    def _build_next_state(self, *, state: dict[str, Any], event: EventRequest, event_sk: str) -> dict[str, Any]:
        next_state = dict(state)
        next_state["status"] = event.status_after
        next_state["updatedAt"] = utc_now_iso()
        next_state["version"] = int(state["version"]) + 1
        next_state["lastEventKey"] = event_sk
        if event.status_after == "processing":
            next_state["progress"] = event.details.get("progress", {"stage": "processing"})
            next_state["error"] = None
        elif event.status_after == "failed":
            next_state["progress"] = event.details.get("progress", {"stage": "failed"})
            next_state["error"] = event.details.get(
                "error",
                {"code": "PROCESSING_FAILED", "message": "Processing failed.", "retryable": True},
            )
        elif event.status_after == "completed":
            next_state["progress"] = event.details.get("progress", {"stage": "completed"})
            next_state["error"] = None
            next_state["results"] = self._build_results(event.details.get("results", {}))
        return next_state

    def _build_event_item(self, *, state: dict[str, Any], event: EventRequest, event_sk: str) -> dict[str, Any]:
        return {
            "PK": f"UPLOAD#{event.upload_id}",
            "SK": event_sk,
            "entityType": "EVENT",
            "uploadId": event.upload_id,
            "sessionId": state["sessionId"],
            "nickname": state.get("nickname"),
            "participantId": state.get("participantId"),
            "eventType": event.event_type,
            "eventTime": event.event_time,
            "producer": event.producer,
            "statusAfter": event.status_after,
            "details": event.details,
            "gsi3pk": build_activity_gsi3pk(str(state["sessionId"])),
            "gsi3sk": build_activity_gsi3sk(event.event_time, event.upload_id, event.event_type),
        }

    def _build_results(self, results: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(results, dict):
            return {}
        faces = results.get("faces", [])
        if not isinstance(faces, list):
            faces = []
        mapped_faces: list[dict[str, Any]] = []
        for face in faces:
            if not isinstance(face, dict):
                continue
            mapped_face = dict(face)
            key = mapped_face.get("key")
            if isinstance(key, str) and key and self._cloudfront_domain:
                mapped_face["url"] = _build_cloudfront_url(self._cloudfront_domain, key)
            mapped_faces.append(mapped_face)
        merged = dict(results)
        merged["faces"] = mapped_faces
        return merged

    @staticmethod
    def _is_idempotent_init(existing_state: dict[str, Any], req: InitRequest) -> bool:
        return (
            existing_state.get("uploadId") == req.upload_id
            and existing_state.get("sessionId") == req.session_id
            and existing_state.get("nickname") == req.nickname
            and existing_state.get("participantId") == req.participant_id
            and existing_state.get("submittedAt") == req.submitted_at
            and existing_state.get("source") == req.source
        )

    @staticmethod
    def _to_status_response(state: dict[str, Any]) -> dict[str, Any]:
        return {
            "uploadId": state.get("uploadId"),
            "status": state.get("status"),
            "sessionId": state.get("sessionId"),
            "nickname": state.get("nickname"),
            "participantId": state.get("participantId"),
            "submittedAt": state.get("submittedAt"),
            "updatedAt": state.get("updatedAt"),
            "progress": state.get("progress"),
            "results": state.get("results"),
            "error": state.get("error"),
        }


def _build_cloudfront_url(cloudfront_domain: str, key: str) -> str:
    domain = cloudfront_domain.strip().rstrip("/")
    key_part = key.lstrip("/")
    if not domain.startswith("http://") and not domain.startswith("https://"):
        domain = f"https://{domain}"
    return f"{domain}/{key_part}"


def _map_activity_outcome(status_after: str) -> str:
    if status_after == "completed":
        return "success"
    if status_after == "failed":
        return "failure"
    if status_after == "processing":
        return "in_progress"
    if status_after == "queued":
        return "queued"
    return "in_progress"

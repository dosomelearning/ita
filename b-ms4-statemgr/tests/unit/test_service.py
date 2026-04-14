from __future__ import annotations

from copy import deepcopy

import pytest

from src.domain import DomainError, build_event_sk
from src.service import StateService


class InMemoryRepository:
    def __init__(self):
        self.states: dict[str, dict] = {}
        self.events: dict[tuple[str, str], dict] = {}

    def get_state(self, upload_id: str):
        state = self.states.get(upload_id)
        return deepcopy(state) if state else None

    def get_event(self, upload_id: str, event_sk: str):
        event = self.events.get((upload_id, event_sk))
        return deepcopy(event) if event else None

    def create_initial_state(self, *, upload_id: str, item: dict):
        if upload_id in self.states:
            raise DomainError(
                code="TERMINAL_STATE_CONFLICT",
                message="Upload state already exists.",
                status_code=409,
                retryable=False,
            )
        self.states[upload_id] = deepcopy(item)

    def apply_event_transition(self, *, upload_id: str, prior_state: dict, next_state: dict, event_item: dict):
        current = self.states.get(upload_id)
        if not current or current["version"] != prior_state["version"]:
            raise DomainError(
                code="DEPENDENCY_UNAVAILABLE",
                message="State transition transaction failed due to concurrent update.",
                status_code=503,
                retryable=True,
            )
        self.events[(upload_id, event_item["SK"])] = deepcopy(event_item)
        self.states[upload_id] = deepcopy(next_state)


def make_service(cloudfront_domain: str = "d111111abcdef8.cloudfront.net") -> StateService:
    return StateService(repository=InMemoryRepository(), cloudfront_domain=cloudfront_domain)


def test_register_upload_init_creates_queued_state():
    service = make_service()
    result = service.register_upload_init(
        {
            "uploadId": "u-1",
            "sessionId": "s-1",
            "submittedAt": "2026-04-14T10:00:00Z",
            "source": "spa",
        }
    )
    assert result["uploadId"] == "u-1"
    assert result["status"] == "queued"
    assert result["results"] is None


def test_register_upload_init_is_idempotent_for_same_payload():
    service = make_service()
    payload = {
        "uploadId": "u-1",
        "sessionId": "s-1",
        "submittedAt": "2026-04-14T10:00:00Z",
        "source": "spa",
    }
    first = service.register_upload_init(payload)
    second = service.register_upload_init(payload)
    assert second["uploadId"] == first["uploadId"]
    assert second["status"] == "queued"


def test_register_upload_init_rejects_conflicting_payload():
    service = make_service()
    service.register_upload_init(
        {
            "uploadId": "u-1",
            "sessionId": "s-1",
            "submittedAt": "2026-04-14T10:00:00Z",
            "source": "spa",
        }
    )
    with pytest.raises(DomainError) as exc:
        service.register_upload_init(
            {
                "uploadId": "u-1",
                "sessionId": "s-2",
                "submittedAt": "2026-04-14T10:00:00Z",
                "source": "spa",
            }
        )
    assert exc.value.code == "TERMINAL_STATE_CONFLICT"


def test_record_processing_event_updates_state():
    service = make_service()
    service.register_upload_init(
        {
            "uploadId": "u-1",
            "sessionId": "s-1",
            "submittedAt": "2026-04-14T10:00:00Z",
            "source": "spa",
        }
    )
    result = service.record_processing_event(
        "u-1",
        {
            "eventType": "detection_completed",
            "eventTime": "2026-04-14T10:02:00Z",
            "producer": "ms2",
            "statusAfter": "processing",
            "details": {"progress": {"stage": "detection_done"}},
        },
    )
    assert result["status"] == "processing"
    assert result["progress"]["stage"] == "detection_done"


def test_record_completed_event_builds_cloudfront_urls():
    service = make_service("https://demo.cloudfront.net")
    service.register_upload_init(
        {
            "uploadId": "u-1",
            "sessionId": "s-1",
            "submittedAt": "2026-04-14T10:00:00Z",
            "source": "spa",
        }
    )
    service.record_processing_event(
        "u-1",
        {
            "eventType": "detection_completed",
            "eventTime": "2026-04-14T10:01:00Z",
            "producer": "ms2",
            "statusAfter": "processing",
            "details": {"progress": {"stage": "processing"}},
        },
    )
    completed = service.record_processing_event(
        "u-1",
        {
            "eventType": "extraction_completed",
            "eventTime": "2026-04-14T10:02:00Z",
            "producer": "ms3",
            "statusAfter": "completed",
            "details": {
                "results": {
                    "faces": [
                        {"faceId": "f1", "bucket": "ita-data", "key": "faces/u-1/f1.jpg"},
                    ]
                }
            },
        },
    )
    assert completed["status"] == "completed"
    assert completed["results"]["faces"][0]["url"] == "https://demo.cloudfront.net/faces/u-1/f1.jpg"


def test_record_event_duplicate_is_idempotent():
    repo = InMemoryRepository()
    service = StateService(repository=repo, cloudfront_domain="")
    service.register_upload_init(
        {
            "uploadId": "u-1",
            "sessionId": "s-1",
            "submittedAt": "2026-04-14T10:00:00Z",
            "source": "spa",
        }
    )
    payload = {
        "eventType": "detection_completed",
        "eventTime": "2026-04-14T10:01:00Z",
        "producer": "ms2",
        "statusAfter": "processing",
        "details": {"progress": {"stage": "processing"}},
    }
    first = service.record_processing_event("u-1", payload)
    second = service.record_processing_event("u-1", payload)
    assert first["status"] == "processing"
    assert second["status"] == "processing"
    event_sk = build_event_sk("2026-04-14T10:01:00Z", "detection_completed", "ms2")
    assert ("u-1", event_sk) in repo.events


def test_get_status_missing_upload():
    service = make_service()
    with pytest.raises(DomainError) as exc:
        service.get_status("missing")
    assert exc.value.code == "UPLOAD_NOT_FOUND"

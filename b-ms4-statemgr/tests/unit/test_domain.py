import pytest

from src.domain import (
    DomainError,
    assert_transition_allowed,
    validate_event_payload,
    validate_init_payload,
)


def test_validate_init_payload_success():
    req = validate_init_payload(
        {
            "uploadId": "u-1",
            "sessionId": "s-1",
            "submittedAt": "2026-04-14T10:00:00Z",
            "source": "spa",
        }
    )
    assert req.upload_id == "u-1"
    assert req.session_id == "s-1"
    assert req.submitted_at == "2026-04-14T10:00:00Z"


def test_validate_init_payload_rejects_source():
    with pytest.raises(DomainError) as exc:
        validate_init_payload(
            {
                "uploadId": "u-1",
                "sessionId": "s-1",
                "submittedAt": "2026-04-14T10:00:00Z",
                "source": "mobile",
            }
        )
    assert exc.value.code == "VALIDATION_ERROR"


def test_validate_event_payload_for_ms2_processing():
    req = validate_event_payload(
        "u-1",
        {
            "eventType": "detection_completed",
            "eventTime": "2026-04-14T10:01:00Z",
            "producer": "ms2",
            "statusAfter": "processing",
            "details": {"progress": {"stage": "detection_done"}},
        },
    )
    assert req.producer == "ms2"
    assert req.status_after == "processing"


def test_validate_event_payload_rejects_invalid_status_for_ms2():
    with pytest.raises(DomainError) as exc:
        validate_event_payload(
            "u-1",
            {
                "eventType": "detection_completed",
                "eventTime": "2026-04-14T10:01:00Z",
                "producer": "ms2",
                "statusAfter": "completed",
                "details": {},
            },
        )
    assert exc.value.code == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "current,next_state,allowed",
    [
        ("queued", "processing", True),
        ("queued", "failed", True),
        ("processing", "completed", True),
        ("processing", "failed", True),
        ("completed", "processing", False),
        ("failed", "processing", False),
    ],
)
def test_transition_guardrails(current, next_state, allowed):
    if allowed:
        assert_transition_allowed(current, next_state)
    else:
        with pytest.raises(DomainError) as exc:
            assert_transition_allowed(current, next_state)
        assert exc.value.code == "INVALID_TRANSITION"

import pytest

from src.domain import (
    DomainError,
    assert_transition_allowed,
    build_activity_gsi3pk,
    build_activity_gsi3sk,
    build_participant_id,
    validate_event_payload,
    validate_init_payload,
)


def test_validate_init_payload_success():
    req = validate_init_payload(
        {
            "uploadId": "u-1",
            "sessionId": "s-1",
            "nickname": "Alice",
            "submittedAt": "2026-04-14T10:00:00Z",
            "source": "spa",
        }
    )
    assert req.upload_id == "u-1"
    assert req.session_id == "s-1"
    assert req.nickname == "Alice"
    assert req.participant_id == "alice"
    assert req.submitted_at == "2026-04-14T10:00:00.000Z"


def test_validate_init_payload_rejects_source():
    with pytest.raises(DomainError) as exc:
        validate_init_payload(
            {
                "uploadId": "u-1",
                "sessionId": "s-1",
                "nickname": "Alice",
                "submittedAt": "2026-04-14T10:00:00Z",
                "source": "mobile",
            }
        )
    assert exc.value.code == "VALIDATION_ERROR"


def test_build_participant_id_normalizes_nickname():
    assert build_participant_id("  Alice   The   Great ") == "alice the great"


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
    assert req.event_time == "2026-04-14T10:01:00.000Z"


def test_validate_event_payload_for_ms2_queued_upload_succeeded():
    req = validate_event_payload(
        "u-1",
        {
            "eventType": "upload_succeeded",
            "eventTime": "2026-04-14T10:00:10Z",
            "producer": "ms2",
            "statusAfter": "queued",
            "details": {"progress": {"stage": "uploaded"}},
        },
    )
    assert req.producer == "ms2"
    assert req.status_after == "queued"


def test_validate_event_payload_for_ms1_queued():
    req = validate_event_payload(
        "u-1",
        {
            "eventType": "upload_init_received",
            "eventTime": "2026-04-14T10:00:00Z",
            "producer": "ms1",
            "statusAfter": "queued",
            "details": {"phase": "pending_upload"},
        },
    )
    assert req.producer == "ms1"
    assert req.status_after == "queued"


def test_activity_gsi_builders():
    assert build_activity_gsi3pk("cr-abc123") == "FEED#CLASS#cr-abc123"
    assert (
        build_activity_gsi3sk("2026-04-15T10:01:00.123Z", "upl-1", "detection_completed")
        == "E#2026-04-15T10:01:00.123Z#U#upl-1#T#detection_completed"
    )


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


def test_validate_event_payload_rejects_invalid_status_for_ms1():
    with pytest.raises(DomainError) as exc:
        validate_event_payload(
            "u-1",
            {
                "eventType": "upload_url_issued",
                "eventTime": "2026-04-14T10:01:00Z",
                "producer": "ms1",
                "statusAfter": "processing",
                "details": {},
            },
        )
    assert exc.value.code == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "current,next_state,allowed",
    [
        ("queued", "queued", True),
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

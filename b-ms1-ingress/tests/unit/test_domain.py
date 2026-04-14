import pytest

from src.domain import IngressError, validate_upload_init_payload


def test_validate_upload_init_payload_success():
    req = validate_upload_init_payload(
        {
            "password": "class2026",
            "nickname": "ava",
            "sessionId": "s-1",
            "contentType": "image/jpeg",
            "fileSizeBytes": 12345,
        }
    )
    assert req.password == "class2026"
    assert req.nickname == "ava"
    assert req.session_id == "s-1"
    assert req.content_type == "image/jpeg"
    assert req.file_size_bytes == 12345


def test_validate_upload_init_payload_rejects_content_type():
    with pytest.raises(IngressError) as exc:
        validate_upload_init_payload(
            {
                "password": "class2026",
                "nickname": "ava",
                "sessionId": "s-1",
                "contentType": "application/pdf",
            }
        )
    assert exc.value.code == "VALIDATION_ERROR"


def test_validate_upload_init_payload_rejects_missing_password():
    with pytest.raises(IngressError) as exc:
        validate_upload_init_payload(
            {
                "nickname": "ava",
                "sessionId": "s-1",
                "contentType": "image/jpeg",
            }
        )
    assert exc.value.code == "VALIDATION_ERROR"

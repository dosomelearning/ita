import pytest

from src.domain import IngressError, validate_upload_init_payload


def test_validate_upload_init_payload_success():
    req = validate_upload_init_payload(
        {
            "password": "class2026!@#",
            "nickname": "ava",
            "sessionId": "s-1",
            "contentType": "image/jpeg",
            "fileSizeBytes": 12345,
        }
    )
    assert req.password == "class2026!@#"
    assert req.nickname == "ava"
    assert req.session_id == "s-1"
    assert req.content_type == "image/jpeg"
    assert req.file_size_bytes == 12345


def test_validate_upload_init_payload_rejects_content_type():
    with pytest.raises(IngressError) as exc:
        validate_upload_init_payload(
            {
                "password": "class2026!@#",
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


def test_validate_upload_init_payload_rejects_invalid_password_format():
    with pytest.raises(IngressError) as exc:
        validate_upload_init_payload(
            {
                "password": "A1 B2C",
                "nickname": "ava",
                "sessionId": "s-1",
                "contentType": "image/jpeg",
            }
        )
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details["field"] == "password"


def test_validate_upload_init_payload_rejects_nickname_starting_with_number():
    with pytest.raises(IngressError) as exc:
        validate_upload_init_payload(
            {
                "password": "AB12CD",
                "nickname": "1ava",
                "sessionId": "s-1",
                "contentType": "image/jpeg",
            }
        )
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details["field"] == "nickname"


def test_validate_upload_init_payload_accepts_special_characters_in_password():
    req = validate_upload_init_payload(
        {
            "password": "A!b#2026$",
            "nickname": "ava",
            "sessionId": "s-1",
            "contentType": "image/jpeg",
        }
    )
    assert req.password == "A!b#2026$"

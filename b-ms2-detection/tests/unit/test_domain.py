import json

import pytest

from src.domain import DetectionError, parse_sqs_body, parse_uploaded_object


def test_parse_sqs_body_returns_records():
    body = json.dumps({"Records": [{"eventSource": "aws:s3"}]})
    records = parse_sqs_body(body)
    assert len(records) == 1


def test_parse_sqs_body_rejects_invalid_json():
    with pytest.raises(DetectionError) as exc:
        parse_sqs_body("{")
    assert exc.value.code == "INVALID_MESSAGE"
    assert exc.value.retryable is False


def test_parse_uploaded_object_success():
    uploaded = parse_uploaded_object(
        {
            "eventSource": "aws:s3",
            "eventName": "ObjectCreated:Put",
            "eventTime": "2026-04-15T10:20:30Z",
            "s3": {
                "bucket": {"name": "ita-data-bucket"},
                "object": {"key": "uploaded%2Fclass-a%2Fupl-1234.jpg"},
            },
        }
    )
    assert uploaded.bucket == "ita-data-bucket"
    assert uploaded.key == "uploaded/class-a/upl-1234.jpg"
    assert uploaded.session_id == "class-a"
    assert uploaded.upload_id == "upl-1234"
    assert uploaded.uploaded_at == "2026-04-15T10:20:30.000Z"


def test_parse_uploaded_object_ignores_non_uploaded_prefix():
    with pytest.raises(DetectionError) as exc:
        parse_uploaded_object(
            {
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": "ita-data-bucket"},
                    "object": {"key": "faces/class-a/upl-1234.jpg"},
                },
            }
        )
    assert exc.value.code == "IGNORED_PREFIX"


def test_parse_uploaded_object_rejects_bad_key_shape():
    with pytest.raises(DetectionError) as exc:
        parse_uploaded_object(
            {
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": "ita-data-bucket"},
                    "object": {"key": "uploaded/class-a/.jpg"},
                },
            }
        )
    assert exc.value.code == "INVALID_KEY_FORMAT"

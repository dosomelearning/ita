from __future__ import annotations

import json

import pytest

from src.api import Ms2Api
from src.domain import DetectionError


class StubService:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def process_sqs_record(self, *, body: str, message_id: str):
        self.calls.append((message_id, body))
        return {"processed": 1, "ignored": 0, "records": 1}


class Context:
    aws_request_id = "req-123"


def test_api_handles_batch_of_sqs_records():
    api = Ms2Api(StubService())
    event = {
        "Records": [
            {
                "messageId": "m-1",
                "body": json.dumps({"Records": [{"eventSource": "aws:s3"}]}),
            }
        ]
    }
    result = api.handle(event, Context())
    assert result["processed"] == 1
    assert result["ignored"] == 0
    assert result["batchRecords"] == 1


def test_api_rejects_missing_records_list():
    api = Ms2Api(StubService())
    with pytest.raises(DetectionError) as exc:
        api.handle({}, Context())
    assert exc.value.code == "INVALID_EVENT"


def test_api_rejects_non_string_body():
    api = Ms2Api(StubService())
    event = {"Records": [{"messageId": "m-1", "body": {"bad": "shape"}}]}
    with pytest.raises(DetectionError) as exc:
        api.handle(event, Context())
    assert exc.value.code == "INVALID_EVENT"

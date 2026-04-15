from __future__ import annotations

import json

import pytest

from src.api import Ms3Api
from src.domain import ExtractionError


class StubService:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def process_sqs_record(self, *, body: str, message_id: str):
        self.calls.append((message_id, body))
        return {"processed": 1}


class Context:
    aws_request_id = "req-123"


def test_api_handles_batch_of_sqs_records():
    api = Ms3Api(StubService())
    event = {
        "Records": [
            {
                "messageId": "m-1",
                "body": json.dumps(
                    {
                        "contractVersion": "faces-extraction.v1",
                        "uploadId": "u-1",
                        "sessionId": "s-1",
                        "sourceBucket": "ita-data",
                        "sourceKey": "processed/faces/s-1/u-1.jpg",
                        "detectionArtifactKey": "rekognition/s-1/u-1.json",
                        "detectedFaces": 1,
                        "eventTime": "2026-04-16T07:00:00Z",
                    }
                ),
            }
        ]
    }
    result = api.handle(event, Context())
    assert result["processed"] == 1
    assert result["batchRecords"] == 1


def test_api_rejects_missing_records_list():
    api = Ms3Api(StubService())
    with pytest.raises(ExtractionError) as exc:
        api.handle({}, Context())
    assert exc.value.code == "INVALID_EVENT"


def test_api_rejects_non_string_body():
    api = Ms3Api(StubService())
    event = {"Records": [{"messageId": "m-1", "body": {"bad": "shape"}}]}
    with pytest.raises(ExtractionError) as exc:
        api.handle(event, Context())
    assert exc.value.code == "INVALID_EVENT"

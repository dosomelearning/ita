from __future__ import annotations

import json

import pytest

from src.domain import ExtractionError, parse_extraction_job


def _valid_body() -> str:
    return json.dumps(
        {
            "contractVersion": "faces-extraction.v1",
            "uploadId": "upl-1",
            "sessionId": "cr-1",
            "sourceBucket": "ita-data",
            "sourceKey": "processed/faces/cr-1/upl-1.jpg",
            "detectionArtifactKey": "rekognition/cr-1/upl-1.json",
            "detectedFaces": 2,
            "eventTime": "2026-04-16T08:00:00Z",
        }
    )


def test_parse_extraction_job_success():
    job = parse_extraction_job(_valid_body())
    assert job.upload_id == "upl-1"
    assert job.event_time == "2026-04-16T08:00:00.000Z"
    assert job.detected_faces == 2


def test_parse_extraction_job_rejects_invalid_contract():
    payload = json.loads(_valid_body())
    payload["contractVersion"] = "faces-extraction.v0"
    with pytest.raises(ExtractionError) as exc:
        parse_extraction_job(json.dumps(payload))
    assert exc.value.code == "UNSUPPORTED_CONTRACT"


def test_parse_extraction_job_requires_detected_faces_positive():
    payload = json.loads(_valid_body())
    payload["detectedFaces"] = 0
    with pytest.raises(ExtractionError) as exc:
        parse_extraction_job(json.dumps(payload))
    assert exc.value.code == "INVALID_MESSAGE"

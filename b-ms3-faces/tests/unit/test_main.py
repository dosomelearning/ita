from __future__ import annotations

import pytest

from src import main


class DummyApi:
    def __init__(self, service):
        self.service = service

    def handle(self, event, context):
        _ = event
        _ = context
        return {"ok": True, "service": type(self.service).__name__}


class DummyService:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyMs4Client:
    def __init__(self, *, base_url: str, region: str):
        self.base_url = base_url
        self.region = region


def test_handler_builds_service_and_returns_api_result(monkeypatch):
    monkeypatch.setattr(main, "_API", None)
    monkeypatch.setattr(main, "_MS4_CLIENT", None)
    monkeypatch.setattr(main, "_S3_CLIENT", object())
    monkeypatch.setenv("PROCESSING_BUCKET_NAME", "ita-data")
    monkeypatch.setenv("MS4_INTERNAL_API_BASE_URL", "https://example.execute-api.eu-central-1.amazonaws.com")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")

    monkeypatch.setattr(main, "Ms3Api", DummyApi)
    monkeypatch.setattr(main, "FacesService", DummyService)
    monkeypatch.setattr(main, "Ms4Client", DummyMs4Client)

    response = main.handler({"Records": []}, None)

    assert response["ok"] is True
    assert response["service"] == "DummyService"


def test_handler_raises_when_required_env_missing(monkeypatch):
    monkeypatch.setattr(main, "_API", None)
    monkeypatch.setattr(main, "_MS4_CLIENT", None)
    monkeypatch.delenv("PROCESSING_BUCKET_NAME", raising=False)
    monkeypatch.setenv("MS4_INTERNAL_API_BASE_URL", "https://example.execute-api.eu-central-1.amazonaws.com")

    with pytest.raises(RuntimeError) as exc:
        main.handler({"Records": []}, None)
    assert "PROCESSING_BUCKET_NAME" in str(exc.value)

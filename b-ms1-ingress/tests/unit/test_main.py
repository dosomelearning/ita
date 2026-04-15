import os

import pytest

from src import main


class DummyApi:
    def handle(self, event, context):
        _ = context
        return {"statusCode": 200, "body": '{"ok":true}', "eventType": type(event).__name__}


def test_handler_delegates_to_cached_api(monkeypatch):
    monkeypatch.setattr(main, "_API", DummyApi())
    response = main.handler({"hello": "world"}, None)
    assert response["statusCode"] == 200


def test_get_api_requires_env(monkeypatch):
    monkeypatch.setattr(main, "_API", None)
    monkeypatch.delenv("SHARED_PASSWORD_SSM_PARAM", raising=False)
    monkeypatch.delenv("PROCESSING_BUCKET_NAME", raising=False)
    monkeypatch.delenv("MS4_INTERNAL_API_BASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        main._get_api()


def test_get_api_builds_dependencies(monkeypatch):
    created = {}

    class FakeMs4Client:
        def __init__(self, *, base_url, region):
            created["ms4_base_url"] = base_url
            created["ms4_region"] = region

    class FakeService:
        def __init__(self, **kwargs):
            created["service_kwargs"] = kwargs

    class FakeApi:
        def __init__(self, service):
            created["api_service"] = service

    monkeypatch.setattr(main, "_API", None)
    monkeypatch.setattr(main, "_MS4_CLIENT", None)
    monkeypatch.setattr(main, "_SSM_CLIENT", object())
    monkeypatch.setattr(main, "_S3_CLIENT", object())
    monkeypatch.setattr(main, "Ms4Client", FakeMs4Client)
    monkeypatch.setattr(main, "IngressService", FakeService)
    monkeypatch.setattr(main, "IngressApi", FakeApi)
    monkeypatch.setenv("SHARED_PASSWORD_SSM_PARAM", "/ita/shared-password")
    monkeypatch.setenv("PROCESSING_BUCKET_NAME", "ita-data")
    monkeypatch.setenv("MS4_INTERNAL_API_BASE_URL", "https://ms4.example")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    monkeypatch.setenv("PRESIGN_EXPIRES_SECONDS", "900")

    api = main._get_api()
    assert api is not None
    assert created["ms4_base_url"] == "https://ms4.example"
    assert created["service_kwargs"]["processing_bucket_name"] == "ita-data"
    assert created["service_kwargs"]["presign_expires_seconds"] == 900
    assert created["service_kwargs"]["shared_password_parameter_name"] == "/ita/shared-password"

    monkeypatch.setattr(main, "_API", None)
    os.environ.pop("SHARED_PASSWORD_SSM_PARAM", None)

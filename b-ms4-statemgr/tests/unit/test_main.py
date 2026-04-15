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


def test_get_api_requires_table_env(monkeypatch):
    monkeypatch.setattr(main, "_API", None)
    monkeypatch.delenv("STATE_TABLE_NAME", raising=False)
    with pytest.raises(RuntimeError) as exc:
        main._get_api()
    assert "STATE_TABLE_NAME" in str(exc.value)


def test_get_api_builds_instance(monkeypatch):
    created = {}

    class FakeRepo:
        def __init__(self, table_name, ddb_client):
            created["table_name"] = table_name
            created["ddb_client"] = ddb_client

    class FakeService:
        def __init__(self, repository, cloudfront_domain):
            created["repository"] = repository
            created["cloudfront_domain"] = cloudfront_domain

    class FakeApi:
        def __init__(self, service):
            created["service"] = service

    monkeypatch.setattr(main, "_API", None)
    monkeypatch.setattr(main, "_DDB_CLIENT", object())
    monkeypatch.setattr(main, "StateRepository", FakeRepo)
    monkeypatch.setattr(main, "StateService", FakeService)
    monkeypatch.setattr(main, "Ms4Api", FakeApi)
    monkeypatch.setenv("STATE_TABLE_NAME", "ms4-state-table")
    monkeypatch.setenv("CLOUDFRONT_DOMAIN", "d111111abcdef8.cloudfront.net")
    api = main._get_api()
    assert api is not None
    assert created["table_name"] == "ms4-state-table"
    assert created["cloudfront_domain"] == "d111111abcdef8.cloudfront.net"
    monkeypatch.setattr(main, "_API", None)
    os.environ.pop("STATE_TABLE_NAME", None)

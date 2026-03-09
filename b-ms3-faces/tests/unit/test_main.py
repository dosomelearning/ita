import json

from src.main import handler


def test_handler_returns_expected_scaffold_payload():
    response = handler({"hello": "world"}, None)

    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["service"] == "ms3-faces"
    assert payload["message"] == "Scaffold lambda placeholder"

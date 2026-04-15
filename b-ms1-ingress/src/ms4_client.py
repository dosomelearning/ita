from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


class Ms4Client:
    def __init__(self, *, base_url: str, region: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._region = region
        self._session = boto3.Session(region_name=region)

    def register_upload_init(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
        url = f"{self._base_url}/internal/uploads/init"
        return self._post_json(url=url, payload=payload)

    def post_event(self, *, upload_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
        url = f"{self._base_url}/internal/uploads/{upload_id}/events"
        return self._post_json(url=url, payload=payload)

    def _post_json(self, *, url: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "Host": _host_from_url(url)}

        aws_request = AWSRequest(method="POST", url=url, data=body, headers=headers)
        credentials = self._session.get_credentials()
        if credentials is None:
            raise RuntimeError("Unable to obtain AWS credentials for MS4 signed request.")
        SigV4Auth(credentials, "execute-api", self._region).add_auth(aws_request)

        request = urllib.request.Request(url=url, method="POST", data=body, headers=dict(aws_request.headers.items()))
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                response_body = response.read().decode("utf-8")
                return response.status, _safe_json(response_body)
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8")
            return exc.code, _safe_json(response_body)


def _host_from_url(url: str) -> str:
    # URL looks like https://host/path...
    return url.split("://", 1)[1].split("/", 1)[0]


def _safe_json(raw: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None

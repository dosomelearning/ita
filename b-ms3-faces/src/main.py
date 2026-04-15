from __future__ import annotations

import logging
import os
from typing import Any

import boto3

try:  # Lambda runtime imports
    from api import Ms3Api
    from ms4_client import Ms4Client
    from service import FacesService
except ImportError:  # Unit tests/package imports
    from .api import Ms3Api
    from .ms4_client import Ms4Client
    from .service import FacesService

logging.getLogger().setLevel(os.getenv("LOG_LEVEL", "INFO"))
_API: Ms3Api | None = None
_MS4_CLIENT: Ms4Client | None = None
_REGION = os.environ.get("AWS_REGION", "eu-central-1")
_S3_CLIENT = boto3.client("s3", region_name=_REGION)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return _get_api().handle(event, context)


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_api() -> Ms3Api:
    global _API
    if _API is None:
        service = FacesService(
            processing_bucket_name=_required_env("PROCESSING_BUCKET_NAME"),
            s3_client=_S3_CLIENT,
            ms4_client=_get_ms4_client(),
        )
        _API = Ms3Api(service)
    return _API


def _get_ms4_client() -> Ms4Client:
    global _MS4_CLIENT
    if _MS4_CLIENT is None:
        _MS4_CLIENT = Ms4Client(base_url=_required_env("MS4_INTERNAL_API_BASE_URL"), region=_REGION)
    return _MS4_CLIENT

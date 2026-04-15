from __future__ import annotations

import logging
import os

import boto3

try:  # Lambda runtime imports
    from api import IngressApi
    from ms4_client import Ms4Client
    from service import IngressService
except ImportError:  # Unit tests/package imports
    from .api import IngressApi
    from .ms4_client import Ms4Client
    from .service import IngressService

_API: IngressApi | None = None
_MS4_CLIENT: Ms4Client | None = None
_REGION = os.environ.get("AWS_REGION", "eu-central-1")
_SSM_CLIENT = boto3.client("ssm", region_name=_REGION)
_S3_CLIENT = boto3.client("s3", region_name=_REGION)

def handler(event, context):
    api = _get_api()
    return api.handle(event, context)


def _get_api() -> IngressApi:
    global _API
    if _API is None:
        _configure_logging()
        shared_password_parameter_name = _required_env("SHARED_PASSWORD_SSM_PARAM")
        processing_bucket = _required_env("PROCESSING_BUCKET_NAME")
        presign_expires_seconds = int(os.environ.get("PRESIGN_EXPIRES_SECONDS", "900"))

        service = IngressService(
            shared_password_parameter_name=shared_password_parameter_name,
            processing_bucket_name=processing_bucket,
            presign_expires_seconds=presign_expires_seconds,
            ssm_client=_SSM_CLIENT,
            s3_client=_S3_CLIENT,
            ms4_client=_get_ms4_client(),
        )
        _API = IngressApi(service=service)
    return _API


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required.")
    return value


def _configure_logging() -> None:
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=level)
    else:
        root_logger.setLevel(level)


def _get_ms4_client() -> Ms4Client:
    global _MS4_CLIENT
    if _MS4_CLIENT is None:
        _MS4_CLIENT = Ms4Client(
            base_url=_required_env("MS4_INTERNAL_API_BASE_URL"),
            region=_REGION,
        )
    return _MS4_CLIENT

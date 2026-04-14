from __future__ import annotations

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

def handler(event, context):
    api = _get_api()
    return api.handle(event, context)


def _get_api() -> IngressApi:
    global _API
    if _API is None:
        shared_password_param = _required_env("SHARED_PASSWORD_SSM_PARAM")
        processing_bucket = _required_env("PROCESSING_BUCKET_NAME")
        ms4_base_url = _required_env("MS4_INTERNAL_API_BASE_URL")
        region = os.environ.get("AWS_REGION", "eu-central-1")
        presign_expires_seconds = int(os.environ.get("PRESIGN_EXPIRES_SECONDS", "900"))

        ssm_client = boto3.client("ssm", region_name=region)
        s3_client = boto3.client("s3", region_name=region)
        ms4_client = Ms4Client(base_url=ms4_base_url, region=region)

        service = IngressService(
            shared_password_parameter_name=shared_password_param,
            processing_bucket_name=processing_bucket,
            presign_expires_seconds=presign_expires_seconds,
            ssm_client=ssm_client,
            s3_client=s3_client,
            ms4_client=ms4_client,
        )
        _API = IngressApi(service=service)
    return _API


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required.")
    return value

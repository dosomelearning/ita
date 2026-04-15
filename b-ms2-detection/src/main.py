from __future__ import annotations

import logging
import os
from typing import Any

import boto3

try:  # Lambda runtime imports
    from api import Ms2Api
    from ms4_client import Ms4Client
    from service import DetectionService
except ImportError:  # Unit tests/package imports
    from .api import Ms2Api
    from .ms4_client import Ms4Client
    from .service import DetectionService

logging.getLogger().setLevel(os.getenv("LOG_LEVEL", "INFO"))


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    region = os.environ.get("AWS_REGION", "eu-central-1")
    processing_bucket_name = _required_env("PROCESSING_BUCKET_NAME")
    faces_extraction_queue_url = _required_env("FACES_EXTRACTION_QUEUE_URL")
    ms4_internal_api_base_url = _required_env("MS4_INTERNAL_API_BASE_URL")

    service = DetectionService(
        processing_bucket_name=processing_bucket_name,
        faces_extraction_queue_url=faces_extraction_queue_url,
        rekognition_client=boto3.client("rekognition", region_name=region),
        s3_client=boto3.client("s3", region_name=region),
        sqs_client=boto3.client("sqs", region_name=region),
        ms4_client=Ms4Client(base_url=ms4_internal_api_base_url, region=region),
    )
    api = Ms2Api(service)
    return api.handle(event, context)


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

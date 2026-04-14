from __future__ import annotations

import os

try:  # Lambda runtime import path
    from api import Ms4Api
    from repository import StateRepository
    from service import StateService
except ImportError:  # Unit tests/package import path
    from .api import Ms4Api
    from .repository import StateRepository
    from .service import StateService

_API: Ms4Api | None = None


def handler(event, context):
    api = _get_api()
    return api.handle(event, context)


def _get_api() -> Ms4Api:
    global _API
    if _API is None:
        table_name = os.environ.get("STATE_TABLE_NAME", "")
        if not table_name:
            raise RuntimeError("STATE_TABLE_NAME environment variable is required.")
        cloudfront_domain = os.environ.get("CLOUDFRONT_DOMAIN", "")
        repository = StateRepository(table_name=table_name)
        service = StateService(repository=repository, cloudfront_domain=cloudfront_domain)
        _API = Ms4Api(service=service)
    return _API

from __future__ import annotations

import logging
from typing import Any

try:  # Lambda runtime imports
    from domain import DetectionError
    from service import DetectionService
except ImportError:  # Unit tests/package imports
    from .domain import DetectionError
    from .service import DetectionService

LOGGER = logging.getLogger(__name__)


class Ms2Api:
    def __init__(self, service: DetectionService) -> None:
        self._service = service

    def handle(self, event: dict[str, Any], context: Any) -> dict[str, Any]:
        records = event.get("Records")
        if not isinstance(records, list):
            raise DetectionError(
                code="INVALID_EVENT",
                message="Lambda event must contain Records list.",
                retryable=False,
            )

        processed = 0
        ignored = 0
        for record in records:
            if not isinstance(record, dict):
                raise DetectionError(
                    code="INVALID_EVENT",
                    message="Each event record must be an object.",
                    retryable=False,
                )
            body = record.get("body")
            if not isinstance(body, str):
                raise DetectionError(
                    code="INVALID_EVENT",
                    message="SQS record body must be a string.",
                    retryable=False,
                )
            message_id = str(record.get("messageId") or "unknown")
            result = self._service.process_sqs_record(body=body, message_id=message_id)
            processed += int(result.get("processed", 0))
            ignored += int(result.get("ignored", 0))

        request_id = getattr(context, "aws_request_id", "unknown-request-id")
        LOGGER.info("MS2 processed SQS batch", extra={"processed": processed, "ignored": ignored, "requestId": request_id})
        return {"processed": processed, "ignored": ignored, "batchRecords": len(records)}

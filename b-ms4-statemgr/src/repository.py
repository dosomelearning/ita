from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import ClientError

try:  # Lambda runtime import path
    from domain import DomainError
except ImportError:  # Unit tests/package import path
    from .domain import DomainError

STATE_SK = "STATE"


class StateRepository:
    def __init__(self, table_name: str, ddb_client: Any | None = None) -> None:
        self._table_name = table_name
        self._ddb = ddb_client or boto3.client("dynamodb")

    def get_state(self, upload_id: str) -> dict[str, Any] | None:
        response = self._ddb.get_item(
            TableName=self._table_name,
            Key=_ddb_key(upload_id, STATE_SK),
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            return None
        return _from_ddb_item(item)

    def get_event(self, upload_id: str, event_sk: str) -> dict[str, Any] | None:
        response = self._ddb.get_item(
            TableName=self._table_name,
            Key=_ddb_key(upload_id, event_sk),
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            return None
        return _from_ddb_item(item)

    def create_initial_state(self, *, upload_id: str, item: dict[str, Any]) -> None:
        ddb_item = _to_ddb_item(item)
        try:
            self._ddb.put_item(
                TableName=self._table_name,
                Item=ddb_item,
                ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
            )
        except ClientError as exc:
            if _is_conditional_failure(exc):
                raise DomainError(
                    code="TERMINAL_STATE_CONFLICT",
                    message="Upload state already exists.",
                    status_code=409,
                    retryable=False,
                    details={"uploadId": upload_id},
                ) from exc
            raise

    def apply_event_transition(
        self,
        *,
        upload_id: str,
        prior_state: dict[str, Any],
        next_state: dict[str, Any],
        event_item: dict[str, Any],
    ) -> None:
        prior_version = int(prior_state["version"])
        next_version = int(next_state["version"])
        event_ddb_item = _to_ddb_item(event_item)
        try:
            self._ddb.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": event_ddb_item,
                            "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                        }
                    },
                    {
                        "Update": {
                            "TableName": self._table_name,
                            "Key": _ddb_key(upload_id, STATE_SK),
                            "ConditionExpression": "#version = :prior_version",
                            "UpdateExpression": (
                                "SET #status = :status, #updatedAt = :updated_at, #version = :next_version, "
                                "#progress = :progress, #results = :results, #error = :error, #lastEventKey = :last_event_key"
                            ),
                            "ExpressionAttributeNames": {
                                "#status": "status",
                                "#updatedAt": "updatedAt",
                                "#version": "version",
                                "#progress": "progress",
                                "#results": "results",
                                "#error": "error",
                                "#lastEventKey": "lastEventKey",
                            },
                            "ExpressionAttributeValues": {
                                ":status": {"S": str(next_state["status"])},
                                ":updated_at": {"S": str(next_state["updatedAt"])},
                                ":next_version": {"N": str(next_version)},
                                ":prior_version": {"N": str(prior_version)},
                                ":progress": _value_to_ddb(next_state.get("progress")),
                                ":results": _value_to_ddb(next_state.get("results")),
                                ":error": _value_to_ddb(next_state.get("error")),
                                ":last_event_key": {"S": str(next_state["lastEventKey"])},
                            },
                        }
                    },
                ]
            )
        except ClientError as exc:
            if _is_transaction_canceled(exc):
                raise DomainError(
                    code="DEPENDENCY_UNAVAILABLE",
                    message="State transition transaction failed due to concurrent update.",
                    status_code=503,
                    retryable=True,
                    details={"uploadId": upload_id},
                ) from exc
            raise

    def list_participant_states(self, *, session_id: str, participant_id: str, limit: int = 20) -> list[dict[str, Any]]:
        response = self._ddb.query(
            TableName=self._table_name,
            IndexName="GSI2",
            KeyConditionExpression="#gsi2pk = :gsi2pk",
            ExpressionAttributeNames={"#gsi2pk": "gsi2pk"},
            ExpressionAttributeValues={
                ":gsi2pk": {"S": f"PARTICIPANT#{session_id}#{participant_id}"},
            },
            ScanIndexForward=False,
            Limit=limit,
        )
        return [_from_ddb_item(item) for item in response.get("Items", [])]

    def list_session_activities(self, *, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        response = self._ddb.query(
            TableName=self._table_name,
            IndexName="GSI3",
            KeyConditionExpression="#gsi3pk = :gsi3pk",
            ExpressionAttributeNames={"#gsi3pk": "gsi3pk"},
            ExpressionAttributeValues={
                ":gsi3pk": {"S": f"FEED#CLASS#{session_id}"},
            },
            ScanIndexForward=False,
            Limit=limit,
        )
        return [_from_ddb_item(item) for item in response.get("Items", [])]


def _ddb_key(upload_id: str, sk: str) -> dict[str, dict[str, str]]:
    return {"PK": {"S": f"UPLOAD#{upload_id}"}, "SK": {"S": sk}}


def _is_conditional_failure(exc: ClientError) -> bool:
    return exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException"


def _is_transaction_canceled(exc: ClientError) -> bool:
    return exc.response.get("Error", {}).get("Code") == "TransactionCanceledException"


def _to_ddb_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: _value_to_ddb(value) for key, value in item.items()}


def _from_ddb_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: _value_from_ddb(value) for key, value in item.items()}


def _value_to_ddb(value: Any) -> dict[str, Any]:
    if value is None:
        return {"NULL": True}
    if isinstance(value, bool):
        return {"BOOL": value}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {"N": str(value)}
    if isinstance(value, str):
        return {"S": value}
    if isinstance(value, list):
        return {"L": [_value_to_ddb(v) for v in value]}
    if isinstance(value, dict):
        return {"M": {k: _value_to_ddb(v) for k, v in value.items()}}
    raise TypeError(f"Unsupported type for DynamoDB conversion: {type(value).__name__}")


def _value_from_ddb(value: dict[str, Any]) -> Any:
    if "S" in value:
        return value["S"]
    if "N" in value:
        num = value["N"]
        return int(num) if num.isdigit() or (num.startswith("-") and num[1:].isdigit()) else float(num)
    if "BOOL" in value:
        return bool(value["BOOL"])
    if "NULL" in value:
        return None
    if "L" in value:
        return [_value_from_ddb(v) for v in value["L"]]
    if "M" in value:
        return {k: _value_from_ddb(v) for k, v in value["M"].items()}
    raise TypeError("Unsupported DynamoDB value shape.")

from src.repository import StateRepository


class StubDdbClient:
    def __init__(self):
        self.last_query = None

    def query(self, **kwargs):
        self.last_query = kwargs
        return {
            "Items": [
                {
                    "PK": {"S": "UPLOAD#u-1"},
                    "SK": {"S": "STATE"},
                    "uploadId": {"S": "u-1"},
                    "status": {"S": "queued"},
                }
            ]
        }


def test_list_participant_states_uses_gsi2_query():
    stub = StubDdbClient()
    repo = StateRepository(table_name="ms4-state", ddb_client=stub)
    result = repo.list_participant_states(session_id="s-1", participant_id="alice", limit=7)

    assert stub.last_query is not None
    assert stub.last_query["IndexName"] == "GSI2"
    assert stub.last_query["Limit"] == 7
    assert stub.last_query["ExpressionAttributeValues"][":gsi2pk"]["S"] == "PARTICIPANT#s-1#alice"
    assert result[0]["uploadId"] == "u-1"

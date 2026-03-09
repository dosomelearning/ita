import json


def handler(event, context):
    _ = context
    body = {
        "service": "ms2-detection",
        "message": "Scaffold lambda placeholder",
        "input_event_type": type(event).__name__,
    }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }

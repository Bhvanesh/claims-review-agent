import json
import logging
from claims_agent.core.logging import JsonFormatter, request_id_var, tenant_id_var

def make_record(message: str)-> logging.LogRecord:
    return logging.LogRecord(name = "test", level=logging.INFO, pathname=__file__, lineno=1, msg=message, args=None, exc_info=None,)

def test_output_is_valid_json():
    data = json.loads(JsonFormatter().format(make_record("hello")))
    assert data["message"] == "hello"
    assert data["level"] == "INFO"

def test_request_id_included():
    token = request_id_var.set("req-123")
    try:
        data = json.loads(JsonFormatter().format(make_record("hi")))
    finally:
        request_id_var.reset(token)
    assert data["request_id"] == "req-123"

def test_request_id_absent_is_null():
    data = json.loads(JsonFormatter().format(make_record("hi")))
    assert data["request_id"] is None
    
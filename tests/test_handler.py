"""Mocked AWS API tests prove no SSM execution and idempotent writes."""
import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import handler


class FakeTable:
    def __init__(self):
        self.calls = []
    def put_item(self, **kwargs):
        self.calls.append(kwargs)


class FakeBoto3(types.ModuleType):
    def __init__(self):
        super().__init__("boto3")
        self.table = FakeTable()
        self.api_clients = []
    def resource(self, name):
        if name != "dynamodb":
            raise AssertionError("Unexpected resource")
        return types.SimpleNamespace(Table=lambda _table: self.table)
    def client(self, name):
        self.api_clients.append(name)
        if name == "sns":
            return types.SimpleNamespace(publish=lambda **kwargs: None)
        raise AssertionError("Unexpected API client: " + name)


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.event = json.loads((ROOT / "examples/cloudwatch-alarm.json").read_text(encoding="utf-8"))
        self.boto = FakeBoto3()
        self.boto_exceptions = types.ModuleType("botocore.exceptions")
        class ClientError(Exception):
            def __init__(self, code):
                self.response = {"Error": {"Code": code}}
        self.boto_exceptions.ClientError = ClientError

    def test_store_record_without_remediation_api(self):
        with patch.dict(sys.modules, {"boto3": self.boto, "botocore": types.ModuleType("botocore"), "botocore.exceptions": self.boto_exceptions}), patch.dict(os.environ, {"INCIDENT_TABLE": "test", "ALARM_PREFIX": "ops-aiops-", "ENABLE_BEDROCK": "false", "NOTIFY_TOPIC_ARN": ""}):
            result = handler.lambda_handler(self.event, None)
        self.assertEqual("RECORDED", result["status"])
        self.assertEqual([], self.boto.api_clients)
        self.assertEqual(1, len(self.boto.table.calls))
        self.assertEqual("attribute_not_exists(event_id)", self.boto.table.calls[0]["ConditionExpression"])

    def test_reject_nonmatching_event_before_api_calls(self):
        self.event["detail"]["alarmName"] = "unauthorized-alarm"
        with patch.dict(sys.modules, {"boto3": self.boto}), patch.dict(os.environ, {"INCIDENT_TABLE": "test"}):
            result = handler.lambda_handler(self.event, None)
        self.assertEqual("IGNORED", result["status"])
        self.assertEqual([], self.boto.api_clients)

    def test_duplicate_event_not_recorded_twice(self):
        def duplicate(**kwargs):
            raise self.boto_exceptions.ClientError("ConditionalCheckFailedException")
        self.boto.table.put_item = duplicate
        with patch.dict(sys.modules, {"boto3": self.boto, "botocore": types.ModuleType("botocore"), "botocore.exceptions": self.boto_exceptions}), patch.dict(os.environ, {"INCIDENT_TABLE": "test", "ENABLE_BEDROCK": "false", "NOTIFY_TOPIC_ARN": ""}):
            result = handler.lambda_handler(self.event, None)
        self.assertEqual("DUPLICATE", result["status"])


if __name__ == "__main__":
    unittest.main()

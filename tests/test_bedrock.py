import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from triage import classify, normalize_event
from bedrock_ai import draft_with_bedrock
import json


class FakeBedrock:
    def __init__(self):
        self.params = None

    def converse(self, **params):
        self.params = params
        return {"output": {"message": {"content": [{"text": "Unverified alarm, please check logs."}]}}}


class BedrockTests(unittest.TestCase):
    def test_prompt_does_not_include_account_or_raw_reason(self):
        event = json.loads((ROOT / "examples/cloudwatch-alarm.json").read_text(encoding="utf-8"))
        event["detail"]["state"]["reason"] = "TOP_SECRET_DO_NOT_SHARE"
        assessment = classify(normalize_event(event))
        fake = FakeBedrock()
        text = draft_with_bedrock(fake, "amazon.nova-lite-v1:0", assessment)
        self.assertIn("Unverified", text)
        serialized = json.dumps(fake.params)
        self.assertNotIn("TOP_SECRET_DO_NOT_SHARE", serialized)
        self.assertNotIn(event["account"], serialized)
        self.assertEqual(220, fake.params["inferenceConfig"]["maxTokens"])


if __name__ == "__main__":
    unittest.main()

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from triage import UnsupportedEvent, classify, normalize_event, safe_summary
from rca import draft_rca


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.event = json.loads((ROOT / "examples/cloudwatch-alarm.json").read_text(encoding="utf-8"))

    def test_synthetic_event_classified_without_execution(self):
        result = classify(normalize_event(self.event))
        self.assertEqual("P2", result["priority"])
        self.assertTrue(result["human_approval_required"])
        self.assertFalse(result["automation_executed"])
        self.assertNotIn("123456789012", safe_summary(result))

    def test_disallow_non_alarm_or_other_source(self):
        self.event["detail"]["state"]["value"] = "OK"
        with self.assertRaises(UnsupportedEvent):
            normalize_event(self.event)
        self.event["detail"]["state"]["value"] = "ALARM"
        self.event["source"] = "aws.s3"
        with self.assertRaises(UnsupportedEvent):
            normalize_event(self.event)

    def test_disallow_unapproved_alarm_prefix(self):
        self.event["detail"]["alarmName"] = "outside-prefix-prod-cpu"
        with self.assertRaises(UnsupportedEvent):
            normalize_event(self.event)

    def test_prod_availability_routes_to_p1(self):
        self.event["detail"]["alarmName"] = "ops-aiops-prod-availability"
        result = classify(normalize_event(self.event))
        self.assertEqual("P1", result["priority"])

    def test_rca_does_not_invent_root_cause(self):
        result = classify(normalize_event(self.event))
        rca = draft_rca(result)
        self.assertIn("Root cause", rca)
        self.assertIn("**Unknown.**", rca)
        self.assertIn("Human sign-off", rca)
        self.assertIn("No corrective action has been performed", rca)


if __name__ == "__main__":
    unittest.main()

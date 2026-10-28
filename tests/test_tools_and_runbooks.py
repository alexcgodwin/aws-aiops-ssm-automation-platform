import datetime as dt
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "scripts"))
from tool_trials import evaluate
from check_runbooks import check


class ProcessTests(unittest.TestCase):
    def test_tool_trial_rejects_poor_security(self):
        data = json.loads((ROOT / "experiments/illustrative-tool-evaluation.json").read_text(encoding="utf-8"))
        results = evaluate(data)
        unsafe = next(item for item in results if item["tool"] == "Unreviewed log forwarder")
        self.assertEqual("reject", unsafe["recommendation"])
        self.assertFalse(unsafe["measured_results_claimed"])

    def test_runbooks_have_owners_and_reviews(self):
        self.assertEqual([], check(as_of=dt.date(2026, 10, 27)))

    def test_runbooks_become_overdue(self):
        self.assertTrue(any("overdue" in s for s in check(as_of=dt.date(2027, 8, 1))))


if __name__ == "__main__":
    unittest.main()

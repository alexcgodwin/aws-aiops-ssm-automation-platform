import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agent_policy import load_policy, authorize


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy(ROOT / "config/agent-permissions.json")

    def test_allowlisted_read_action(self):
        r = authorize(self.policy, "triage-assistant", "read_alarm_metadata")
        self.assertTrue(r["allow"])
        self.assertFalse(r["execution_performed"])

    def test_reject_unknown_agent_and_action(self):
        self.assertFalse(authorize(self.policy, "mystery", "read_alarm_metadata")["allow"])
        self.assertFalse(authorize(self.policy, "triage-assistant", "ec2_reboot")["allow"])

    def test_sensitive_request_needs_explicit_approval(self):
        agent, action = "maintenance-operator", "request_runbook_execution"
        self.assertFalse(authorize(self.policy, agent, action)["allow"])
        self.assertFalse(authorize(self.policy, agent, action, approved=True)["allow"])
        approved = authorize(self.policy, agent, action, approved=True, approval_reference="CHG-123")
        self.assertTrue(approved["allow"])
        self.assertTrue(approved["requires_approval"])
        self.assertFalse(approved["execution_performed"])


if __name__ == "__main__":
    unittest.main()

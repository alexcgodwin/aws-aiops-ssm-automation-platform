"""Policy decision engine. No tool execution or automatic remediation."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping


def load_policy(path: str | Path) -> dict[str, Any]:
    policy = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(policy, dict) or "agents" not in policy:
        raise ValueError("Invalid agent policy document")
    return policy


def authorize(
    policy: Mapping[str, Any], agent: str, action: str, *,
    approved: bool = False, approval_reference: str | None = None
) -> dict[str, Any]:
    config = policy.get("agents", {}).get(agent)
    if not isinstance(config, dict):
        return {"allow": False, "reason": "unknown_agent", "requires_approval": False}
    permitted = set(config.get("allowed_actions", []))
    if action not in permitted:
        return {"allow": False, "reason": "action_not_allowlisted", "requires_approval": False}
    gated = action in set(config.get("approval_required", []))
    if gated and not (approved and approval_reference and approval_reference.strip()):
        return {"allow": False, "reason": "approval_required", "requires_approval": True}
    return {
        "allow": True,
        "reason": "policy_permitted",
        "requires_approval": gated,
        "approval_reference": approval_reference if gated else None,
        "execution_performed": False,
    }

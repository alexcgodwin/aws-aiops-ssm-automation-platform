"""Deterministic CloudWatch alert triage. No AWS credentials required."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


class UnsupportedEvent(ValueError):
    """Event is not an allowed CloudWatch ALARM transition."""


@dataclass(frozen=True)
class Alert:
    event_id: str
    alarm: str
    timestamp: str
    region: str
    account: str
    state: str


def normalize_event(event: Mapping[str, Any], prefix: str = "ops-aiops-") -> Alert:
    if not isinstance(event, dict):
        raise UnsupportedEvent("Expected EventBridge event object")
    if event.get("source") != "aws.cloudwatch":
        raise UnsupportedEvent("Unsupported event source")
    if event.get("detail-type") != "CloudWatch Alarm State Change":
        raise UnsupportedEvent("Unsupported detail type")
    detail = event.get("detail")
    if not isinstance(detail, dict):
        raise UnsupportedEvent("Missing detail")
    state = detail.get("state", {})
    if not isinstance(state, dict) or state.get("value") != "ALARM":
        raise UnsupportedEvent("Only ALARM transitions are processed")
    alarm = detail.get("alarmName")
    if not isinstance(alarm, str) or not alarm.startswith(prefix):
        raise UnsupportedEvent("Alarm outside the approved prefix")
    if len(alarm) > 255 or not re.fullmatch(r"[a-zA-Z0-9_.:/-]+", alarm):
        raise UnsupportedEvent("Invalid alarm identifier")
    event_id = event.get("id")
    if not isinstance(event_id, str) or not re.fullmatch(r"[a-zA-Z0-9-]{8,80}", event_id):
        raise UnsupportedEvent("Invalid event identifier")
    for name in ("time", "region", "account"):
        if not isinstance(event.get(name), str) or len(event[name]) > 80:
            raise UnsupportedEvent(f"Missing or invalid {name}")
    return Alert(
        event_id=event_id,
        alarm=alarm,
        timestamp=event["time"],
        region=event["region"],
        account=event["account"],
        state="ALARM",
    )


def classify(alert: Alert) -> dict[str, Any]:
    """Decision support, not a service-level incident severity authority."""
    name = alert.alarm.casefold()
    signals: list[str] = []
    score = 25
    if any(t in name for t in ("availability", "unhealthy", "5xx", "outage")):
        score += 45
        signals.append("availability_keyword")
    if any(t in name for t in ("prod", "production", "critical")):
        score += 20
        signals.append("production_keyword_unverified")
    if any(t in name for t in ("cpu", "memory", "disk", "latency")):
        score += 15
        signals.append("resource_pressure_keyword")
    score = min(score, 100)
    priority = "P1" if score >= 80 else "P2" if score >= 55 else "P3"
    return {
        "event_id": alert.event_id,
        "alarm": alert.alarm,
        "observed_at": alert.timestamp,
        "region": alert.region,
        "priority": priority,
        "risk_score": score,
        "signals": signals,
        "status": "NEEDS_HUMAN_REVIEW",
        "automation_executed": False,
        "human_approval_required": True,
    }


def safe_summary(assessment: Mapping[str, Any]) -> str:
    return (
        f"Alarm {assessment['alarm']} triggered at {assessment['observed_at']}. "
        f"Deterministic triage: {assessment['priority']} ({assessment['risk_score']}/100). "
        "This is an unverified signal. Review metrics, recent changes, affected "
        "services, and customer impact. Do not execute remediation without approval."
    )

"""EventBridge -> deterministic triage -> DynamoDB ledger -> optional SNS/Bedrock.

This Lambda has no SSM mutation permissions and cannot invoke runbooks.
"""
from __future__ import annotations
import json
import os
import time
from typing import Any

from bedrock_ai import draft_with_bedrock
from rca import draft_rca
from triage import UnsupportedEvent, classify, normalize_event, safe_summary


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    prefix = os.environ.get("ALARM_PREFIX", "ops-aiops-")
    try:
        alert = normalize_event(event, prefix=prefix)
    except UnsupportedEvent:
        # Explicitly rejected events are benign; no DynamoDB or Bedrock API calls.
        return {"status": "IGNORED"}

    assessment = classify(alert)
    report = safe_summary(assessment)
    ai_mode = "disabled"
    if os.environ.get("ENABLE_BEDROCK", "false").lower() == "true":
        try:
            import boto3
            client = boto3.client("bedrock-runtime")
            report = draft_with_bedrock(client, os.environ["BEDROCK_MODEL_ID"], assessment)
            ai_mode = "draft_unverified"
        except Exception as exc:
            # Never put exception (which may contain sensitive request context) in logs.
            print(json.dumps({"event_id": alert.event_id, "ai_mode": "fallback", "error_type": type(exc).__name__}))
            ai_mode = "fallback"
    rca = draft_rca(assessment, report if ai_mode == "draft_unverified" else None)
    import boto3
    from botocore.exceptions import ClientError

    table = boto3.resource("dynamodb").Table(os.environ["INCIDENT_TABLE"])
    item = {
        "event_id": alert.event_id,
        "alarm": assessment["alarm"],
        "observed_at": assessment["observed_at"],
        "region": assessment["region"],
        "priority": assessment["priority"],
        "risk_score": assessment["risk_score"],
        "status": "NEEDS_HUMAN_REVIEW",
        "mode": ai_mode,
        "summary": report[:1600],
        "rca_draft": rca[:3900],
        "expires_at": int(time.time()) + int(os.environ.get("RETENTION_DAYS", "30")) * 86400,
    }
    try:
        table.put_item(Item=item, ConditionExpression="attribute_not_exists(event_id)")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return {"status": "DUPLICATE", "event_id": alert.event_id}
        raise

    topic = os.environ.get("NOTIFY_TOPIC_ARN")
    if topic:
        boto3.client("sns").publish(
            TopicArn=topic,
            Subject=f"AIOps {assessment['priority']} alert (review required)"[:100],
            Message=json.dumps({
                "event_id": alert.event_id,
                "alarm": alert.alarm,
                "priority": assessment["priority"],
                "message": "Review required. No automated remediation.",
            }),
        )
    print(json.dumps({
        "event_id": alert.event_id,
        "status": "RECORDED",
        "priority": assessment["priority"],
        "ai_mode": ai_mode,
        "automation_executed": False,
    }))
    return {"status": "RECORDED", "event_id": alert.event_id, "priority": assessment["priority"]}

"""Draft incident reports with explicit evidence gaps and review controls."""
from __future__ import annotations
from typing import Any, Mapping


def draft_rca(assessment: Mapping[str, Any], ai_draft: str | None = None) -> str:
    # No hallucinated cause or recovery statement: unknowns are first-class fields.
    event_id = assessment["event_id"]
    alarm = assessment["alarm"]
    time = assessment["observed_at"]
    source = "Optional Bedrock draft (unverified)" if ai_draft else "Deterministic template"
    narrative = ai_draft or (
        "The alarm entered ALARM. This does not establish customer impact, "
        "root cause, or a successful remediation."
    )
    return f"""# Draft Incident RCA — {event_id}

**Status:** DRAFT — NOT VERIFIED
**Alarm:** {alarm}
**First observed:** {time}
**Suggested triage priority:** {assessment['priority']}
**Draft source:** {source}
**Approval:** Incident commander / service owner required

## What we observed
{narrative}

## Customer impact
Unknown. Validate affected services, users, and duration.

## Timeline
- {time}: CloudWatch alarm transition was received.
- Investigation, mitigation, and recovery timestamps: **not yet established**.

## Root cause
**Unknown.** Do not assert a cause until corroborated by metrics, logs, traces, and change history.

## Evidence to collect
- Alarm history and time-series metrics.
- CloudTrail / deployment history and infrastructure configuration changes.
- Application logs, traces, and downstream dependency signals.
- SSM Automation execution ID, approver, and verification results *if run*.

## Recovery and verification
No corrective action has been performed by this reporting tool.
Record the authorized change, validation probes, and rollback outcome separately.

## Follow-up actions
- Confirm incident scope and assign an owner.
- Verify suspected cause using independently sourced evidence.
- Capture change approval, recovery verification, and review sign-off.

**Human sign-off:** Pending
""";

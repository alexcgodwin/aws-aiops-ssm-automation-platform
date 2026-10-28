# Runbook: CloudWatch incident triage and draft RCA

**Owner:** SRE / Cloud Operations
**Last reviewed:** 2026-10-27
**Approval:** An incident commander approves production remediation.
**Rollback:** Revert only an approved, recorded infrastructure change and verify service health.

1. Locate the CloudWatch alarm transition and event ID. Validate it against current metric data and affected service ownership.
2. Confirm EventBridge rule matching, Lambda execution and DynamoDB incident record. Check SQS DLQ for undelivered events.
3. Compare correlated deployments, CloudTrail audit data, metrics, logs and affected dependencies; record evidence timestamps.
4. Run the local RCA draft tool only with a sanitized synthetic or approved incident object; verify all assertions manually.
5. Assign severity based on actual customer impact, not the example risk score alone.
6. Request change approval, record scope, expected blast radius, backout plan and on-call owners.
7. If remediation is approved, run the designated SSM Automation separately as an authorized operator. Do not let AI invoke it.
8. Confirm recovery from independent application-level probes and update the final RCA with sign-off.

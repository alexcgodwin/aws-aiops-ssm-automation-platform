# Operations: ownership, signals, and recovery

## Day-2 checks

- Verify CloudWatch alarm volumes, alarm-prefix changes and EventBridge rule matching.
- Monitor Lambda Errors/Throttles and EventBridge DLQ depth; investigate before redrive.
- Confirm incident record schema, deduplication, TTL, log retention and SNS delivery failures.
- Review SSM managed-node inventory, patch compliance, failed commands and session access.
- Validate human approval workflow quarterly using a disposable canary; record runbook execution IDs.
- Measure detection-to-triage time, false positives, cost per incident, patch scan compliance and authorized recovery time. Do not claim improvement without a baseline.

## Incident lifecycle

Detection → deterministic triage → optional draft → human verification → scoped change approval → SSM execution when appropriate → recovery probes → peer-reviewed RCA → runbook updates in Git.

## Severity

Scores are heuristics derived from alarm names and are not a substitute for blast radius, customer impact or ownership. P1/P2/P3 route guidance can be overridden by the incident commander with recorded justification.

## Ownership

The platform owner maintains Terraform IAM and SSM policies. The service owner reviews customer impact and change safety. The identity/operations lead approves runbook execution. Detection engineers maintain false-positive controls. All maintenance runbooks require an owner and a 180-day review date.

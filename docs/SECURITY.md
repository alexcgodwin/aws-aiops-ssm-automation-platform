# Threat model and agent access controls

| Threat | Guardrail | Residual risk |
| --- | --- | --- |
| Injected instructions in alarm text | Triage ignores CloudWatch reason; AI is draft-only and uses a strict system prompt | Bedrock-generated narrative may still be inaccurate |
| Identity privilege escalation | Lambda has no EC2 or SSM write permissions | An over-privileged human may still start manual runbooks |
| Unauthorized reboot | `aws:approve` step + EC2 resource-tag condition on `RebootInstances` | Approver authority must be managed outside this repo |
| Unapproved maintenance | Maintenance window opt-in; task performs `Scan`, not `Install` | Manually altered windows may run with broader roles |
| Exposed server access | No inbound SSH, no public IP, SSM instance role, IMDSv2 | SSM endpoint/IAM compromise still matters |
| Event flood / AI cost | Alarm prefix, Lambda concurrency=2, Bedrock off by default | Alarm volume, DynamoDB and logs can still incur costs |
| Secrets in incident output | No raw event dump; bounded prompt, SNS only sanitized metadata | Alarm naming may inadvertently contain sensitive data |
| Duplicate alerts | DynamoDB conditional PutItem | SNS delivery may be retried; downstream dedup still recommended |
| Malicious repository change | CI read-only and no cloud credentials; CODEOWNERS file | Admins must configure required reviews / branch protection in GitHub |

## Agent policy

`config/agent-permissions.json` defines tool-action allowances per named agent. `src/agent_policy.py` is a **decision function only**; allowing an action in that policy does not grant AWS IAM rights and does not call the action. Real agent implementations must enforce the allowlist at tool boundaries, log approvals and decisions in an access-controlled audit system, use short-lived credentials, and gate all changes separately.

## SSM Automation approval

AWS `aws:approve` requires an authorized user or role principal and an SNS topic. This runbook takes an `ApproverArn` at execution and uses an `Automation-` prefixed topic for notifications. Subscribe the designated approver manually, review their permissions, and verify approval behavior in an isolated account before production use. Do not treat an SNS message by itself as an authorization record.

## Terraform state

Provision a separately managed S3 state bucket with SSE, versioning, IAM controls and S3 lockfile configuration (or an explicitly documented equivalent). Never commit state, plans or credential files. Avoid managing foundational state infrastructure inside the state it protects.

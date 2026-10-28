# Architecture and engineering decisions

The AIOps operations plane is separate from the AWS Systems Manager control plane. Inbound alarms are untrusted signals and do not confer privileges on the decision engine.

## Control plane boundaries

1. **CloudWatch/EventBridge** accepts only matching name prefixes and the `ALARM` transition. Events may be duplicated; treat EventBridge as at-least-once delivery.
2. **Lambda triage** has only exact permissions for its log group, DynamoDB PutItem, and optional SNS Publish / exact Bedrock model invocation. There is no SSM, IAM, or EC2 write role on this process.
3. **DynamoDB** stores incident draft and severity. The event id is an idempotency key. Operational fact checking happens outside the AI output. TTL deletes eventually, not immediately.
4. **SSM Automation** has an IAM service role permitting DescribeInstances and `RebootInstances` on tagged instances only. The Automation document enforces a human approval checkpoint; operators need explicit `StartAutomationExecution` permissions separately.
5. **EC2 private fleet** has no inbound security-group rules, no key pair, no public IP, encrypted root volume, IMDSv2, SSM core role and endpoint-only network route. The private interface endpoints cost money.
6. **Patch operations** are policy-driven; the maintenance window is disabled by default and its task uses `Operation=Scan`. Installation requires an approved separate process.

## Cross-account expansion path

A production AWS Organizations rollout should use an audit/operations account, resource accounts, and separately reviewed EventBridge cross-account forwarding policies for each approved account/region. The included implementation is **single-account**; no cross-account permissions or central event-bus claims are made. Extend with explicit `aws:PrincipalOrgID` restrictions, bus policies, rate quotas, cross-region event forwarding and state isolation only after validation.

## Data governance

A CloudWatch alarm can include sensitive `reason` fields. The reference engine intentionally ignores raw reason strings when preparing Bedrock prompts and SNS messages. It uses bounded names and derived numeric scoring. This still requires a data-classification review prior to real AI use. Store only sanitized incident data and review monitoring, access, retention and audit requirements.

## Failure and concurrency model

EventBridge target retries are bounded and failed delivery goes to SQS DLQ. Lambda and DynamoDB runtime errors are not silently suppressed. Incident deduplication is by EventBridge event ID. If optional Bedrock fails, the handler falls back to deterministic guidance. Initial Bedrock requests may be charged; review TPS and IAM conditions. Monitor DLQ depth, Lambda Errors/Throttles, CloudWatch Logs costs and table usage.

## Non-goals

No fully autonomous remediation, no orchestration of SSM across an organization, no automatic patch installation, no live CloudTrail creation, and no claimed compliance certification or benchmark metrics.

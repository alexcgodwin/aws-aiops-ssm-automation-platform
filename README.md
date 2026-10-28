# AWS Enterprise AIOps & Systems Manager Automation Platform

> **Senior-level AWS operations engineering reference** — incident triage, approval-gated SSM runbooks, private session access, patch governance, optional Bedrock-assisted RCA drafts and measured tool-selection methodology.

[![CI](https://github.com/alexcgodwin/aws-aiops-ssm-automation-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/alexcgodwin/aws-aiops-ssm-automation-platform/actions/workflows/ci.yml)
![AWS](https://img.shields.io/badge/AWS-Operations-FF9900)
![Terraform](https://img.shields.io/badge/Terraform-6.x_provider-7B42BC)
![Security](https://img.shields.io/badge/Security-Approval_First-207E54)

## Engineering problem

Alerting alone cannot diagnose what changed, whether a service is affected, or what it is safe to do next. A production operations platform needs bounded evidence collection, accountable approvals, reversible remediation, repeatable fleet access, predictable costs, and post-incident learning. This project connects those requirements without granting AI an infrastructure-change role.

**Status:** Source-code reference implementation. Offline validation and CI do **not** prove cloud deployment or operational effectiveness. No AWS resources have been deployed by this project. Applying Terraform creates billable AWS resources, even when optional Bedrock, EC2, and patch windows remain disabled.

## Architecture and decision boundaries

```text
CloudWatch alarm (approved alarm-name prefix, ALARM transition)
      |
      v
Amazon EventBridge rule ----> target retry + encrypted SQS DLQ
      |
      v
AWS Lambda (dedicated least-privilege triage IAM role)
      |--- deterministic scoring, bounded metadata, no shell/SSM actions
      |--- optional Amazon Bedrock draft (OFF by default)
      |--- DynamoDB incident ledger (idempotent key + TTL)
      +--- optional sanitized SNS notification (OFF by default)
      |
      v
SOC / SRE operator reviews draft RCA and corroborates evidence
      |
      v
Separate SSM Automation runbook (NOT callable by triage Lambda)
      |--- Describe target
      |--- aws:approve human approval gate (SNS approval topic)
      +--- RebootInstances only if IAM EC2 resource tag allows
      |
      v
Operator verifies recovery, records impact, publishes reviewed RCA

Optional private fleet (OFF by default)
EC2 with IMDSv2 + SSM core role + no inbound SSH
  |--- private interface endpoints: ssm / ssmmessages / ec2messages
  |--- S3 gateway endpoint
  +--- SSM Patch Manager baseline + optional scan-only maintenance window
```

## Implemented components

| Domain | Implementation | Operating constraint |
| --- | --- | --- |
| Detection pipeline | CloudWatch ALARM → EventBridge → Lambda | Only alarms matching configured name prefix |
| Incident analysis | Deterministic severity classifier and RCA draft | Evidence gaps explicitly marked; no invented cause |
| AI-assisted narratives | Optional Bedrock Converse API | Off by default; model/region access and cost approval required |
| Event resilience | EventBridge retry policy, SSE-SQS dead-letter queue | Operators must inspect and redrive safely |
| Incident audit | DynamoDB event-id deduplication, TTL, CloudWatch logs | TTL is asynchronous, not a hard retention guarantee |
| Secure notifications | Optional SNS incident topic | No subscribers provisioned by default |
| Agent security | Explicit allowlisted policy, approval flags, no direct execute calls | Separate IAM identities for triage vs automation |
| Systems Manager Automation | Manual `aws:approve` + tag-gated EC2 reboot | Not invoked by alert triage, approvers assigned at execution |
| Fleet management | Optional private EC2, interface endpoints, SSM instance role | Cloud resources disabled by default; endpoints are billable |
| Patch operations | AL2023 patch baseline + opt-in scan-only maintenance window | No automatic patch installation |
| Tool evaluation | Weighted security/cost/reliability rubric | Example scores explicitly synthetic, not measured |
| Runbook upkeep | Reviewer/owner/approval/rollback metadata and 180-day CI check | Changes require pull requests |
| Delivery controls | Terraform fmt/init/validate, Python tests, hygiene checks | CI has no AWS credentials and never applies Terraform |

## Repository layout

```text
.github/workflows/ci.yml       Read-only tests and Terraform validation
terraform/operations/         AWS events, incident ledger, SSM, IAM, patching
terraform/fleet/              Optional private EC2 and SSM VPC endpoints
src/                          Lambda handler, deterministic triage, Bedrock drafts, RCA, agent policy
tests/                        Behavioral regression tests
config/agent-permissions.json  Explicit tool-action allowlist and approval policy
examples/                     Synthetic CloudWatch event
experiments/                  Illustrative weighted tool evaluations
scripts/                      Offline CLI, hygiene check, runbook freshness test
docs/                         Architecture, threat model, rollout, cost, runbooks, ADRs
```

## Quick start — zero cloud usage

Python 3.10+ and Terraform 1.6+:

```bash
python -m unittest discover -s tests -v
python scripts/aiops_cli.py triage
python scripts/aiops_cli.py rca
python scripts/aiops_cli.py tool-trial
python scripts/check_runbooks.py
python scripts/check_repository.py
terraform fmt -check -recursive terraform
terraform -chdir=terraform/operations init -backend=false
terraform -chdir=terraform/operations validate
terraform -chdir=terraform/fleet init -backend=false
terraform -chdir=terraform/fleet validate
```

No cloud credentials are needed for the commands above. Terraform provider download requires internet access.

## Deployment strategy

The recommended adoption order is **offline tests → protected remote state → approved, reviewed Terraform plan → operations stack → observed low-risk alarm test → optional private fleet → SSM Session Manager test → scan-only patch compliance → human-reviewed Automation rehearsal**. Only then consider optional Bedrock narratives, and do not enable any paid option without cost authorization.

See [deployment](docs/DEPLOYMENT.md), [security](docs/SECURITY.md), [architecture](docs/ARCHITECTURE.md), [cost](docs/COST.md), and [operating procedures](docs/OPERATIONS.md). The operations account and workload accounts should use separate AWS IAM roles, remote Terraform state keys and account-level guardrails.

## Security position

**This is not an autonomous remediation agent.** Bedrock is only permitted to draft text. The Lambda IAM role cannot call `ssm:StartAutomationExecution`, restart EC2, or execute arbitrary commands. The SSM Automation role can reboot only an explicitly tagged EC2 instance *after* the `aws:approve` step. An operator initiates the runbook. Security and business impact decisions remain with humans.

## Portfolio evidence limits

CI validates schemas, formatting, unit tests and design invariants. This repository includes **no live incident, measured MTTR improvement, verified Bedrock model invocation, executed SSM reboot, or performance comparison**. Any such outcomes must be supported by tenant-specific measurements and evidence.

### Authoritative sources

- [CloudWatch alarm events on EventBridge](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-and-eventbridge.html)
- [SSM Automation approvals](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-action-approve.html)
- [SSM Patch Manager maintenance windows](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-patch-scheduletasks.html)
- [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-call.html)

MIT licensed. © 2026 Alex Godwin.

# Controlled deployment playbook

**No Azure, AWS, or GCP resources have been deployed by this GitHub reference.** These steps must run only in an explicitly approved sandbox or operations AWS account. Charges apply for Lambda, CloudWatch, DynamoDB, S3 and any optional VPC endpoints, EC2, SSM features or Bedrock calls.

## Prerequisites

- AWS account/region ownership, budget alerts, applicable service quotas and an access-controlled Terraform role.
- Terraform >=1.6 and AWS CLI v2 with permission boundaries; `aws sts get-caller-identity` must show the intended account.
- Hardened S3 remote state pre-created by a platform owner, with isolated `operations` and `fleet` keys and lockfile controls.
- An identified human change approver and subscribed **Automation** approval topic for SSM runbooks.
- A documented data classification policy before invoking Bedrock or shipping alarm metadata.

## Offline tests

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

## Infrastructure change procedure

1. Review permissions, account, region, expected chargeable resources and change window.
2. Copy `terraform/operations/terraform.tfvars.example` to ignored `terraform.tfvars` and set approved values.
3. Configure reviewed S3 backend by copying `backend.tf.example` to `backend.tf` and using an untracked `backend.hcl`. Run `terraform init -backend-config=backend.hcl` (after verifying your state bucket and encryption).
4. Run `terraform plan -out=planfile` and review `terraform show planfile` for any unexpected changes. Protect plan files and do not publish them.
5. Require change approval before `terraform apply planfile`. Do not run CI-based apply.
6. Verify EventBridge name-prefix filtering, incident table dedup, CloudWatch metrics, DLQ health, SNS permissions, and SSM document creation.
7. Submit a synthetic `ALARM` for an isolated canary, ensure exactly one incident record is stored and no AWS remediation is performed.
8. Enable **fleet** stack only after approving billed interface endpoints/EC2, isolated private networking and region support for relevant SSM endpoints. Verify `aws ssm describe-instance-information` and then `aws ssm start-session --target <instance-id>` from an authorized operator identity.
9. Optionally enable scan-only maintenance window after patch-group/OS compatibility review. Validate compliance reports; no Install task is included.
10. Rehearse SSM reboot only on a disposable, tagged canary with designated approver and audit trail; verify the EC2 action is denied if `AIOpsRebootApproved` is not `true`.
11. Optional Bedrock: check model access, region, IAM model ARN, prompt governance and budget. Enable only in the approved account, then validate the first request and log evidence.

## Verification and cleanup

Capture approval ID, Terraform plan, AWS account, change window, CloudWatch events, Lambda result, DynamoDB record, and SSM Automation execution history. Delete canary EC2 and endpoints when no longer needed. Do not destroy incident records under legal hold. Reconcile Terraform state and revoke operator permissions after exercises.

**CLI does not connect to AWS:** `python scripts/aiops_cli.py` is an offline demonstration only.

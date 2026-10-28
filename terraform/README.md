# Terraform stacks

`operations/` provisions EventBridge filtering, Lambda AIOps triage, incident DynamoDB, bounded SNS notifications, event DLQ, a tag-scoped approval-only reboot document, and an AL2023 patch baseline. Paid Bedrock, canary monitoring, and maintenance-window scans default to disabled.

`fleet/` provisions nothing by default; enabling it creates one private EC2 instance, SSM endpoints, an S3 gateway endpoint, an IAM instance profile, IMDSv2, encrypted gp3 storage, and no inbound SSH. Endpoint hourly charges and EC2 costs apply.

Use separate backend keys and least-privilege Terraform operator identities. The `backend.tf.example` and `backend.hcl.example` files are examples, not active configurations.

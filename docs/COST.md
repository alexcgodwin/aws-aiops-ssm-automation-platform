# Cost controls and safe defaults

Terraform defaults provision an AWS operations baseline, **not a zero-cost sandbox**. CloudWatch Logs, Lambda calls, DynamoDB requests/storage, SNS publishes and EventBridge/SQS services have service-specific pricing and allowances. Always verify current AWS prices and account free-tier eligibility before applying.

Optional features are off by default: Bedrock text drafts, automatic incident SNS publishing, EC2 canary, EC2 alarm, and scheduled SSM patch scans. The private fleet uses multiple interface VPC endpoints; **those can incur hourly and data-processing charges even when the instance is idle**. EC2 and EBS are also billable.

Before applying: obtain a cost owner, use AWS Budgets and alerts, set resource tags, review quotas and estimate incident event rates and model tokens. Cap Lambda concurrency and retention, but do not equate these controls with a hard spending limit. Destroy temporary compute and endpoints after validation.

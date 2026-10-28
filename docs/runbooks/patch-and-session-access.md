# Runbook: SSM Session Manager and patch compliance

**Owner:** Platform Operations / Endpoint Security
**Last reviewed:** 2026-10-27
**Approval:** Change owner approves maintenance window activation and any patch installation.
**Rollback:** Disable the maintenance window and use documented AMI/EBS recovery strategy; patch rollback is not automatic.

1. Confirm target instance belongs to the correct account, private subnet and patch group. Review intended change window.
2. Verify SSM Agent registration, IAM instance role, VPC endpoints and CloudWatch region.
3. Start an operator-authorized SSM session. Session Manager requires separate IAM session permissions; this repository grants none to human principals.
4. Confirm maintenance-window task uses `Operation=Scan` and concurrency/error thresholds.
5. Review reported missing patches, OS compatibility, exceptions and maintenance scheduling; do not automatically install.
6. Any patch installation requires its own peer-reviewed change and restore plan. Do not infer rollback from a successful scan.

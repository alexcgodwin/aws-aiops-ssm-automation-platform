# Runbook: Approval-gated EC2 reboot

**Owner:** SRE Incident Commander
**Last reviewed:** 2026-10-27
**Approval:** Designated IAM approver must approve the `aws:approve` step after checking blast radius.
**Rollback:** If service fails after reboot, follow application failover and instance recovery procedures; a reboot is not directly reversible.

1. Validate that the EC2 instance is a disposable canary or an explicitly authorized production target and tagged `AIOpsRebootApproved=true`.
2. Identify change ticket, service owner, customer impact risk, maintenance window, backups and recovery plan.
3. Have a permitted operator manually start the `ops-aiops-<env>-approved-ec2-reboot` SSM Automation document with the instance ID and approved IAM principal ARN.
4. Review the `DescribeTarget` step and the `aws:approve` waiting status. Subscribe the approver to the `Automation-` SNS topic ahead of time.
5. The designated approver accepts or denies through Systems Manager. The tag-scoped Automation role is a second independent boundary.
6. After execution, validate system status, SSM connectivity, critical services, synthetic probes and incident impact. Capture the Automation execution ID, decision, logs and timestamps.
7. If the target is not tagged eligible or a person denies approval, no reboot is permitted. Escalate to the incident commander for alternative recovery.

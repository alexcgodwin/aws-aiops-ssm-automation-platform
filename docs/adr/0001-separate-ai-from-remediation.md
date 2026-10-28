# ADR-001: Separate AI drafting from remediation

**Status:** Accepted, 2026-10-27

AI-generated text can be wrong or attacker-influenced. The Bedrock tool is optional and returns narrative drafts only. The Lambda IAM role has no EC2, IAM or Systems Manager write permissions. SSM Automation uses a separate identity and human approval. This increases the manual operational burden while limiting privilege escalation and unintended outages.

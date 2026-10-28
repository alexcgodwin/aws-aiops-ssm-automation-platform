# ADR-002: Make paid and state-changing options explicit

**Status:** Accepted, 2026-10-27

Bedrock, private EC2 fleet, patch scheduling and demonstration CloudWatch alarms are disabled by default. The base operations platform is still potentially chargeable; nothing is deployed by CI. Change approval, a protected Terraform backend, canary verification and budget alerts are required before live use.

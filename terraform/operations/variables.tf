variable "aws_region" {
  type    = string
  default = "ca-central-1"
}
variable "project" {
  type    = string
  default = "ops-aiops"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project))
    error_message = "Use a short lowercase letters/numbers/hyphens project prefix."
  }
}
variable "environment" {
  type    = string
  default = "dev"
  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test or prod."
  }
}
variable "alarm_prefix" {
  type        = string
  default     = "ops-aiops-"
  description = "Only matching CloudWatch alarms will be triaged."
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}-$", var.alarm_prefix))
    error_message = "Use a lowercase, hyphen-delimited alarm prefix ending in a hyphen."
  }
}
variable "enable_bedrock" {
  type        = bool
  default     = false
  description = "Chargeable AI draft generation; disabled by default."
}
variable "bedrock_model_id" {
  type        = string
  default     = "amazon.nova-lite-v1:0"
  description = "Verify model access in the selected AWS Region before enabling."
}
variable "enable_incident_notifications" {
  type        = bool
  default     = false
  description = "Allow sanitized incident notifications via SNS."
}
variable "retention_days" {
  type    = number
  default = 30
  validation {
    condition     = var.retention_days >= 7 && var.retention_days <= 365
    error_message = "retention_days must be 7 to 365."
  }
}
variable "enable_patch_window" {
  type        = bool
  default     = false
  description = "Weekly scan-only SSM maintenance window."
}
variable "patch_group" {
  type    = string
  default = "aiops-canary"
}
variable "enable_demo_alarm" {
  type        = bool
  default     = false
  description = "Optional EC2 CPU alarm for an existing test instance."
}
variable "demo_instance_id" {
  type    = string
  default = ""
}
variable "tags" {
  type = map(string)
  default = {
    Owner      = "platform-engineering"
    CostCenter = "cloud-operations"
    DataClass  = "internal"
  }
}

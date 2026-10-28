resource "aws_ssm_patch_baseline" "al2023" {
  name             = "${local.prefix}-al2023-security-baseline"
  description      = "Amazon Linux 2023 security classification, approved after seven days."
  operating_system = "AMAZON_LINUX_2023"
  approval_rule {
    approve_after_days  = 7
    compliance_level    = "HIGH"
    enable_non_security = false
    patch_filter {
      key    = "CLASSIFICATION"
      values = ["Security"]
    }
  }
}
resource "aws_ssm_patch_group" "canary" {
  baseline_id = aws_ssm_patch_baseline.al2023.id
  patch_group = var.patch_group
}
# A scan-only maintenance window is an explicit opt-in.
resource "aws_ssm_maintenance_window" "scan" {
  count                      = var.enable_patch_window ? 1 : 0
  name                       = "${local.prefix}-weekly-patch-scan"
  schedule                   = "cron(0 3 ? * SUN *)"
  schedule_timezone          = "UTC"
  duration                   = 3
  cutoff                     = 1
  allow_unassociated_targets = false
}
resource "aws_ssm_maintenance_window_target" "canary" {
  count         = var.enable_patch_window ? 1 : 0
  window_id     = aws_ssm_maintenance_window.scan[0].id
  name          = "${local.prefix}-patch-group-target"
  resource_type = "INSTANCE"
  targets {
    key    = "tag:Patch Group"
    values = [var.patch_group]
  }
}
resource "aws_ssm_maintenance_window_task" "scan" {
  count           = var.enable_patch_window ? 1 : 0
  window_id       = aws_ssm_maintenance_window.scan[0].id
  name            = "${local.prefix}-run-patch-baseline-scan"
  task_type       = "RUN_COMMAND"
  task_arn        = "AWS-RunPatchBaseline"
  priority        = 10
  max_concurrency = "1"
  max_errors      = "0"
  targets {
    key    = "WindowTargetIds"
    values = [aws_ssm_maintenance_window_target.canary[0].id]
  }
  task_invocation_parameters {
    run_command_parameters {
      parameter {
        name   = "Operation"
        values = ["Scan"]
      }
    }
  }
}

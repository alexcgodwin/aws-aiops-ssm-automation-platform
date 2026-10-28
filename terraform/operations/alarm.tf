resource "aws_cloudwatch_metric_alarm" "canary_cpu" {
  count               = var.enable_demo_alarm ? 1 : 0
  alarm_name          = "${var.alarm_prefix}${var.environment}-cpu"
  alarm_description   = "Existing opt-in EC2 canary: CPU threshold."
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  comparison_operator = "GreaterThanThreshold"
  statistic           = "Average"
  evaluation_periods  = 3
  period              = 300
  threshold           = 85
  treat_missing_data  = "notBreaching"
  alarm_actions       = []
  ok_actions          = []
  dimensions          = { InstanceId = var.demo_instance_id }
  lifecycle {
    precondition {
      condition     = !var.enable_demo_alarm || can(regex("^i-[0-9a-f]{8,17}$", var.demo_instance_id))
      error_message = "Provide existing valid demo_instance_id when enabling an alarm."
    }
  }
}

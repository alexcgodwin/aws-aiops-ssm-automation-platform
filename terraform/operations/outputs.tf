output "event_rule_arn" { value = aws_cloudwatch_event_rule.alarm_transition.arn }
output "triage_lambda_name" { value = aws_lambda_function.triage.function_name }
output "incident_table_name" { value = aws_dynamodb_table.incidents.name }
output "dead_letter_queue_arn" { value = aws_sqs_queue.event_dlq.arn }
output "incident_topic_arn" { value = aws_sns_topic.incident.arn }
output "automation_approvals_topic_arn" { value = aws_sns_topic.automation_approval.arn }
output "approved_reboot_runbook" { value = aws_ssm_document.approved_reboot.name }
output "patch_baseline_id" { value = aws_ssm_patch_baseline.al2023.id }

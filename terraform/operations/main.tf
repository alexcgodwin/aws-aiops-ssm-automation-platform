data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
locals {
  prefix = "${var.project}-${var.environment}"
}
resource "aws_dynamodb_table" "incidents" {
  name         = "${local.prefix}-incident-ledger"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "event_id"
  attribute {
    name = "event_id"
    type = "S"
  }
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  server_side_encryption {
    enabled = true
  }
  point_in_time_recovery {
    enabled = false
  }
}
resource "aws_sns_topic" "incident" {
  name = "${local.prefix}-alerts"
}
resource "aws_sns_topic" "automation_approval" {
  name = "Automation-${local.prefix}-approval"
}
resource "aws_cloudwatch_log_group" "triage" {
  name              = "/aws/lambda/${local.prefix}-triage"
  retention_in_days = 14
}
data "archive_file" "lambda_bundle" {
  type        = "zip"
  source_dir  = "${path.module}/../../src"
  output_path = "${path.module}/triage-lambda.zip"
}
resource "aws_lambda_function" "triage" {
  function_name                  = "${local.prefix}-triage"
  role                           = aws_iam_role.triage.arn
  filename                       = data.archive_file.lambda_bundle.output_path
  source_code_hash               = data.archive_file.lambda_bundle.output_base64sha256
  handler                        = "handler.lambda_handler"
  runtime                        = "python3.12"
  architectures                  = ["x86_64"]
  timeout                        = 30
  memory_size                    = 256
  reserved_concurrent_executions = 2
  environment {
    variables = {
      INCIDENT_TABLE   = aws_dynamodb_table.incidents.name
      ALARM_PREFIX     = var.alarm_prefix
      RETENTION_DAYS   = tostring(var.retention_days)
      ENABLE_BEDROCK   = tostring(var.enable_bedrock)
      BEDROCK_MODEL_ID = var.bedrock_model_id
      NOTIFY_TOPIC_ARN = var.enable_incident_notifications ? aws_sns_topic.incident.arn : ""
    }
  }
  depends_on = [aws_cloudwatch_log_group.triage]
}
resource "aws_sqs_queue" "event_dlq" {
  name                      = "${local.prefix}-event-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}
resource "aws_cloudwatch_event_rule" "alarm_transition" {
  name        = "${local.prefix}-cloudwatch-alarms"
  description = "Only approved-prefix ALARM transitions"
  event_pattern = jsonencode({
    source        = ["aws.cloudwatch"]
    "detail-type" = ["CloudWatch Alarm State Change"]
    detail = {
      alarmName = [{ prefix = var.alarm_prefix }]
      state     = { value = ["ALARM"] }
    }
  })
}
resource "aws_sqs_queue_policy" "event_dlq" {
  queue_url = aws_sqs_queue.event_dlq.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowEventBridgeFailuresOnly"
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.event_dlq.arn
      Condition = {
        ArnEquals = { "aws:SourceArn" = aws_cloudwatch_event_rule.alarm_transition.arn }
      }
    }]
  })
}
resource "aws_cloudwatch_event_target" "triage" {
  rule      = aws_cloudwatch_event_rule.alarm_transition.name
  target_id = "RestrictedTriageLambda"
  arn       = aws_lambda_function.triage.arn
  dead_letter_config {
    arn = aws_sqs_queue.event_dlq.arn
  }
  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 3
  }
  depends_on = [aws_sqs_queue_policy.event_dlq]
}
resource "aws_lambda_permission" "from_eventbridge" {
  statement_id  = "AllowRestrictedEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.triage.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.alarm_transition.arn
}

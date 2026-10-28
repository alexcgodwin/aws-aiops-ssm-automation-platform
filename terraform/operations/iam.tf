data "aws_iam_policy_document" "triage_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}
resource "aws_iam_role" "triage" {
  name               = "${local.prefix}-triage-role"
  assume_role_policy = data.aws_iam_policy_document.triage_assume.json
}
data "aws_iam_policy_document" "triage" {
  statement {
    sid       = "WriteOnlyOwnLambdaLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.triage.arn}:*"]
  }
  statement {
    sid       = "PutOnlyIncidentRecords"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.incidents.arn]
  }
  dynamic "statement" {
    for_each = var.enable_incident_notifications ? [1] : []
    content {
      sid       = "PublishOnlySanitizedNotifications"
      actions   = ["sns:Publish"]
      resources = [aws_sns_topic.incident.arn]
    }
  }
  dynamic "statement" {
    for_each = var.enable_bedrock ? [1] : []
    content {
      sid       = "InvokeOnlyApprovedFoundationModel"
      actions   = ["bedrock:InvokeModel"]
      resources = ["arn:${data.aws_partition.current.partition}:bedrock:${var.aws_region}::foundation-model/${var.bedrock_model_id}"]
    }
  }
}
resource "aws_iam_role_policy" "triage" {
  name   = "${local.prefix}-triage-restricted"
  role   = aws_iam_role.triage.id
  policy = data.aws_iam_policy_document.triage.json
}
data "aws_iam_policy_document" "automation_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ssm.amazonaws.com"]
    }
  }
}
resource "aws_iam_role" "automation" {
  name               = "${local.prefix}-approved-automation"
  assume_role_policy = data.aws_iam_policy_document.automation_assume.json
}
data "aws_iam_policy_document" "automation" {
  statement {
    sid       = "DescribeBeforeAction"
    actions   = ["ec2:DescribeInstances"]
    resources = ["*"]
  }
  statement {
    sid       = "OnlyTaggedInstancesCanReboot"
    actions   = ["ec2:RebootInstances"]
    resources = ["arn:${data.aws_partition.current.partition}:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/*"]
    condition {
      test     = "StringEquals"
      variable = "ec2:ResourceTag/AIOpsRebootApproved"
      values   = ["true"]
    }
  }
  statement {
    sid       = "ApprovalNotificationsOnly"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.automation_approval.arn]
  }
}
resource "aws_iam_role_policy" "automation" {
  name   = "${local.prefix}-approved-runbook"
  role   = aws_iam_role.automation.id
  policy = data.aws_iam_policy_document.automation.json
}

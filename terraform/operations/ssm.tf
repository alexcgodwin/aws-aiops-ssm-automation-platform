# An operator must manually start Automation and supply the approval principal.
# The alert triage Lambda has NO permission to start any SSM Automation.
resource "aws_ssm_document" "approved_reboot" {
  name            = "${local.prefix}-approved-ec2-reboot"
  document_type   = "Automation"
  document_format = "JSON"
  content = jsonencode({
    schemaVersion = "0.3"
    description   = "Manual human-approved reboot; IAM also requires AIOpsRebootApproved=true instance tag."
    assumeRole    = aws_iam_role.automation.arn
    parameters = {
      InstanceId = {
        type        = "String"
        description = "Existing EC2 instance with the required approval tag."
      }
      ApproverArn = {
        type        = "String"
        description = "Authorized approver IAM user or role ARN."
      }
    }
    mainSteps = [
      {
        name   = "DescribeTarget"
        action = "aws:executeAwsApi"
        inputs = {
          Service     = "ec2"
          Api         = "DescribeInstances"
          InstanceIds = ["{{ InstanceId }}"]
        }
      },
      {
        name           = "RequireHumanApproval"
        action         = "aws:approve"
        timeoutSeconds = 604800
        inputs = {
          NotificationArn      = aws_sns_topic.automation_approval.arn
          Message              = "Review impact and change ticket. The target requires AIOpsRebootApproved=true."
          MinRequiredApprovals = 1
          Approvers            = ["{{ ApproverArn }}"]
        }
      },
      {
        name   = "RebootEligibleInstance"
        action = "aws:executeAwsApi"
        inputs = {
          Service     = "ec2"
          Api         = "RebootInstances"
          InstanceIds = ["{{ InstanceId }}"]
        }
      }
    ]
  })
}

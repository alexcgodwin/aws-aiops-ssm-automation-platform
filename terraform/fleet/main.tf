# Optional private EC2 reference fleet. Nothing is created by default.
data "aws_availability_zones" "available" { state = "available" }
data "aws_ssm_parameter" "al2023_ami" {
  count = var.enable_canary ? 1 : 0
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
resource "aws_vpc" "canary" {
  count                = var.enable_canary ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "aiops-private-fleet" }
}
resource "aws_subnet" "private" {
  count                   = var.enable_canary ? 1 : 0
  vpc_id                  = aws_vpc.canary[0].id
  cidr_block              = var.subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = false
  tags                    = { Name = "aiops-private-canary" }
}
resource "aws_route_table" "private" {
  count  = var.enable_canary ? 1 : 0
  vpc_id = aws_vpc.canary[0].id
}
resource "aws_route_table_association" "private" {
  count          = var.enable_canary ? 1 : 0
  subnet_id      = aws_subnet.private[0].id
  route_table_id = aws_route_table.private[0].id
}
resource "aws_security_group" "instance" {
  count       = var.enable_canary ? 1 : 0
  name        = "aiops-canary-ec2"
  description = "No inbound rules; SSM sessions use outbound 443"
  vpc_id      = aws_vpc.canary[0].id
}
resource "aws_vpc_security_group_egress_rule" "instance_https" {
  count             = var.enable_canary ? 1 : 0
  security_group_id = aws_security_group.instance[0].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "TLS egress; private route table restricts reachable destinations"
}
resource "aws_security_group" "endpoints" {
  count       = var.enable_canary ? 1 : 0
  name        = "aiops-canary-vpc-endpoints"
  description = "Allow SSM API TLS only from canary security group"
  vpc_id      = aws_vpc.canary[0].id
}
resource "aws_vpc_security_group_ingress_rule" "endpoint_tls" {
  count                        = var.enable_canary ? 1 : 0
  security_group_id            = aws_security_group.endpoints[0].id
  referenced_security_group_id = aws_security_group.instance[0].id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  description                  = "SSM agent calls via private endpoints"
}
resource "aws_vpc_endpoint" "ssm" {
  for_each            = var.enable_canary ? toset(["ssm", "ssmmessages", "ec2messages"]) : toset([])
  vpc_id              = aws_vpc.canary[0].id
  service_name        = "com.amazonaws.${var.aws_region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.endpoints[0].id]
  subnet_ids          = [aws_subnet.private[0].id]
  tags                = { Name = "aiops-${each.key}" }
}
resource "aws_vpc_endpoint" "s3" {
  count             = var.enable_canary ? 1 : 0
  vpc_id            = aws_vpc.canary[0].id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private[0].id]
}
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}
resource "aws_iam_role" "instance" {
  count              = var.enable_canary ? 1 : 0
  name               = "aiops-canary-ssm-instance"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}
resource "aws_iam_role_policy_attachment" "ssm" {
  count      = var.enable_canary ? 1 : 0
  role       = aws_iam_role.instance[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
resource "aws_iam_instance_profile" "instance" {
  count = var.enable_canary ? 1 : 0
  name  = "aiops-canary-ssm-instance"
  role  = aws_iam_role.instance[0].name
}
resource "aws_instance" "canary" {
  count                       = var.enable_canary ? 1 : 0
  ami                         = data.aws_ssm_parameter.al2023_ami[0].value
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.private[0].id
  vpc_security_group_ids      = [aws_security_group.instance[0].id]
  iam_instance_profile        = aws_iam_instance_profile.instance[0].name
  associate_public_ip_address = false
  monitoring                  = true
  metadata_options {
    http_tokens                 = "required"
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 1
  }
  root_block_device {
    volume_type = "gp3"
    volume_size = 12
    encrypted   = true
  }
  tags = {
    Name                = "aiops-private-canary"
    "Patch Group"       = var.patch_group
    AIOpsRebootApproved = tostring(var.allow_approved_reboot)
    ManagedBy           = "Terraform"
  }
  depends_on = [aws_vpc_endpoint.ssm, aws_vpc_endpoint.s3, aws_iam_role_policy_attachment.ssm]
}
output "canary_instance_id" {
  value       = try(aws_instance.canary[0].id, null)
  description = "Use aws ssm start-session --target INSTANCE_ID after creating the private canary."
}
output "vpc_id" { value = try(aws_vpc.canary[0].id, null) }

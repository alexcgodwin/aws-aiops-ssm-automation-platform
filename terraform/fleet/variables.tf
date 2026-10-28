variable "aws_region" {
  type    = string
  default = "ca-central-1"
}
variable "enable_canary" {
  type        = bool
  default     = false
  description = "Paid VPC endpoints + EC2; explicit opt-in only."
}
variable "instance_type" {
  type    = string
  default = "t3.micro"
}
variable "patch_group" {
  type    = string
  default = "aiops-canary"
}
variable "allow_approved_reboot" {
  type        = bool
  default     = false
  description = "Opt-in tag for approval-gated reboot."
}
variable "vpc_cidr" {
  type    = string
  default = "10.78.0.0/16"
}
variable "subnet_cidr" {
  type    = string
  default = "10.78.10.0/24"
}

variable "aws_region" {
  description = "Primary AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "bpi-platform"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "db_username" {
  type      = string
  default   = "bpi_admin"
  sensitive = true
}

variable "db_password" {
  description = "RDS master password. Pass via TF_VAR_db_password env var, never commit it."
  type        = string
  sensitive   = true
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "api_image_tag" {
  description = "Container image tag for the FastAPI backend (pushed to ECR before apply)"
  type        = string
  default     = "latest"
}

variable "fargate_desired_count" {
  type    = number
  default = 1
}

variable "fargate_cpu" {
  type    = number
  default = 256
}

variable "fargate_memory" {
  type    = number
  default = 512
}

variable "db_instance_class" {
  description = "Small/free-tier-friendly by default; bump for real load"
  type        = string
  default     = "db.t3.micro"
}

variable "alert_email" {
  description = "Email to receive CloudWatch alarm notifications"
  type        = string
}

variable "tags" {
  type = map(string)
  default = {
    Project = "AI-Powered-Business-Performance-Intelligence"
    Course  = "Cloud Computing and Architecture"
  }
}

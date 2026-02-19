variable "environment" {
  description = "Environment: dev, staging, prod"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "Linode region (us-east, us-west, eu-west, etc.)"
  type        = string
  default     = "us-east"
}

variable "cluster_label" {
  description = "LKE cluster name"
  type        = string
  default     = "incident-copilot"
}

variable "linode_token" {
  type        = string
  description = "Linode API token"
  sensitive   = true
}

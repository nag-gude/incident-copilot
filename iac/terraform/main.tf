# Incident Copilot - Linode LKE Infrastructure (IaC)
# Akamai DeveloperWeek 2026 Hackathon
#
# Prerequisites: LINODE_TOKEN env var
# Usage: terraform init && terraform plan && terraform apply

terraform {
  required_providers {
    linode = {
      source  = "linode/linode"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}

provider "linode" {
  token = var.linode_token
}

resource "linode_lke_cluster" "incident_copilot" {
  label       = "${var.cluster_label}-${var.environment}"
  k8s_version = "1.30"
  region      = var.region

  pool {
    type  = "g6-standard-2"
    count = 2
  }

  tags = ["incident-copilot", "hackathon", var.environment]
}


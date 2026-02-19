#!/bin/bash
# Incident Copilot - Provision Linode LKE cluster via Terraform
# Usage: ./deploy/provision-lke.sh [dev|staging|prod]
# Requires: terraform, TF_VAR_linode_token or LINODE_TOKEN

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
IAC_DIR="$ROOT/iac/terraform"
ENV="${1:-dev}"

cd "$IAC_DIR"

# Use LINODE_TOKEN if TF_VAR_linode_token not set
if [ -z "${TF_VAR_linode_token:-}" ] && [ -n "${LINODE_TOKEN:-}" ]; then
  export TF_VAR_linode_token="$LINODE_TOKEN"
fi

if [ -z "${TF_VAR_linode_token:-}" ]; then
  echo "Error: Set LINODE_TOKEN or TF_VAR_linode_token"
  exit 1
fi

echo "=== Provisioning LKE cluster for $ENV ==="
terraform init
terraform plan -var="environment=$ENV" -out=tfplan
terraform apply tfplan

echo ""
echo "=== Save kubeconfig ==="
terraform output -raw kubeconfig > "$ROOT/kubeconfig-$ENV.yaml" 2>/dev/null || true
echo "Kubeconfig saved to $ROOT/kubeconfig-$ENV.yaml"
echo ""
echo "To use: export KUBECONFIG=$ROOT/kubeconfig-$ENV.yaml"
echo "Then: ./deploy/deploy.sh $ENV build"

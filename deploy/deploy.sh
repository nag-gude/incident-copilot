#!/bin/bash
# Incident Copilot - Deploy to Kubernetes (LKE or any K8s)
# Usage: ./deploy/deploy.sh [dev|staging|prod] [build]
# Set KUBECONFIG or ensure kubectl context is configured for target cluster

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ENV="${1:-dev}"
DO_BUILD="${2:-}"

cd "$ROOT"
export IMAGE_TAG="${IMAGE_TAG:-$ENV}"

echo "=== Incident Copilot - Deploy to $ENV ==="

# Build images if requested
if [ "$DO_BUILD" = "build" ]; then
  echo "Building Docker images..."
  "$SCRIPT_DIR/build-and-push.sh" "$ENV"
fi

# Merge env-specific values
VALUES_FILE="$SCRIPT_DIR/envs/${ENV}.yaml"
EXTRA_VALUES="-f ./helm/values.yaml"
if [ -f "$VALUES_FILE" ]; then
  EXTRA_VALUES="$EXTRA_VALUES -f $VALUES_FILE"
  echo "Using values from $VALUES_FILE"
fi

# Helm upgrade/install
helm upgrade --install incident-copilot ./helm \
  -n incident-copilot \
  --create-namespace \
  $EXTRA_VALUES \
  --set imageTag="$IMAGE_TAG" \
  --wait --timeout 5m

echo ""
echo "=== Deployment complete ==="
echo "Get API Gateway endpoint:"
echo "  kubectl get svc api-gateway -n incident-copilot"
echo ""
echo "Port-forward for local access:"
echo "  kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot"

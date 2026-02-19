#!/bin/bash
# Incident Copilot - Deploy to Minikube (build with host Docker, load images, deploy)
# Usage: ./deploy/deploy-minikube.sh [dev|staging|prod]
# Avoids Docker API version mismatch when host client is older than Minikube's daemon.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ENV="${1:-dev}"
IMAGE_TAG="${IMAGE_TAG:-$ENV}"

cd "$ROOT"

SERVICES="ingestion anomaly prediction recommendation knowledge api-gateway"

echo "=== Incident Copilot - Deploy to Minikube ($ENV) ==="

# Unset minikube docker env so we build with host Docker (avoids API version mismatch)
if command -v minikube &>/dev/null; then
  eval $(minikube docker-env -u 2>/dev/null) || true
fi

# Build with host Docker (no REGISTRY)
echo "Building images with host Docker..."
export REGISTRY=""
"$SCRIPT_DIR/build-and-push.sh" "$ENV"

# Load images into Minikube
echo "Loading images into Minikube..."
for svc in $SERVICES; do
  IMG="incident-copilot/${svc}:${IMAGE_TAG}"
  echo "  Loading $IMG..."
  minikube image load "$IMG"
done

# Deploy with Helm (same as deploy.sh, no build step)
export IMAGE_TAG="$IMAGE_TAG"
VALUES_FILE="$SCRIPT_DIR/envs/${ENV}.yaml"
EXTRA_VALUES="-f ./helm/values.yaml"
if [ -f "$VALUES_FILE" ]; then
  EXTRA_VALUES="$EXTRA_VALUES -f $VALUES_FILE"
  echo "Using values from $VALUES_FILE"
fi

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

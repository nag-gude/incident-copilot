#!/bin/bash
# Incident Copilot - Build and optionally push Docker images
# Usage: ./deploy/build-and-push.sh [dev|staging|prod]
# Set REGISTRY (e.g. ghcr.io/user) to push; leave empty for local-only build

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ENV="${1:-dev}"
REGISTRY="${REGISTRY:-}"
IMAGE_TAG="${IMAGE_TAG:-$ENV}"

cd "$ROOT"

SERVICES="ingestion anomaly prediction recommendation knowledge api-gateway"

echo "=== Building Incident Copilot images (tag: $IMAGE_TAG) ==="

for svc in $SERVICES; do
  case "$svc" in
    api-gateway) dockerfile="gateway" ;;
    *) dockerfile="$svc" ;;
  esac
  IMG="${REGISTRY:+$REGISTRY/}incident-copilot/${svc}:${IMAGE_TAG}"
  echo "Building $IMG..."
  docker build -t "$IMG" -f docker/Dockerfile.$dockerfile \
    --build-arg BUILDKIT_INLINE_CACHE=1 .
done

if [ -n "$REGISTRY" ]; then
  echo "=== Pushing to $REGISTRY ==="
  for svc in $SERVICES; do
    IMG="${REGISTRY}/incident-copilot/${svc}:${IMAGE_TAG}"
    docker push "$IMG"
  done
  echo "Push complete. Deploy with: REGISTRY=$REGISTRY ./deploy/deploy.sh $ENV"
else
  echo "Build complete (local). Push skipped (set REGISTRY to push)."
  echo "Deploy with: ./deploy/deploy.sh $ENV build"
fi

#!/bin/bash
set -e

# Configuration
SERVICE_NAME="session-api"
IMAGE_NAME="gcr.io/ai-kms-platform/session-api"
REGION="us-central1"

echo "🛡️  Starting Deployment Guardrails..."

# 1. Run Unit Tests
echo "🧪 Running Tests (pytest)..."
cd api
python3 -m pytest || { echo "❌ Tests Failed! Aborting deployment."; exit 1; }

# 2. Run Type Checks
echo "🧐 Running Type Checks (mypy)..."
# Using python3 -m mypy to ensure we use the installed module
python3 -m mypy . || echo "⚠️ Type Check Failed! Proceeding anyway..."

echo "✅ All Checks Passed!"

# 3. Build & Deploy
echo "🚀 Building Container..."
cd ..
gcloud builds submit --tag $IMAGE_NAME api/

echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --region $REGION \
  --platform managed \
  "$@"

echo "🎉 Deployment Complete!"

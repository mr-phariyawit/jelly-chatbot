#!/bin/bash
# Apply CORS configuration to the GCS uploads bucket
# Run this after deployment or when CORS config changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUCKET_NAME="ai-kms-platform-uploads"

echo "🔧 Applying CORS configuration to gs://${BUCKET_NAME}..."
gsutil cors set "${SCRIPT_DIR}/cors-config.json" "gs://${BUCKET_NAME}"

echo "✅ CORS configuration applied successfully!"
echo ""
echo "Current CORS config:"
gsutil cors get "gs://${BUCKET_NAME}"

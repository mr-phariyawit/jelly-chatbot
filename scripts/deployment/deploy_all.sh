#!/bin/bash
set -e

# Configuration
PROJECT_ID="ai-kms-platform"
REGION="us-central1"
API_SERVICE="session-api"
DASHBOARD_SERVICE="admin-dashboard-service" # Adjust if named differently

echo "🚀 Starting Full Stack Deployment..."

# 1. Deploy API
echo "----------------------------------------"
echo "📦 Deploying Backend (API)..."
cd api
# Run tests first
python3 -m pytest || { echo "❌ API Tests Failed!"; exit 1; }

# Submit build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$API_SERVICE .

# Deploy Cloud Run
gcloud run deploy $API_SERVICE \
  --image gcr.io/$PROJECT_ID/$API_SERVICE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances $PROJECT_ID:$REGION:ai-support-db \
  --update-env-vars "SUPER_ADMIN_EMAILS=mr.phariyawit@gmail.com"

cd ..

# 2. Deploy Dashboard
echo "----------------------------------------"
echo "🖥️  Deploying Frontend (Dashboard)..."
cd admin-dashboard

# Build & Deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$DASHBOARD_SERVICE .
gcloud run deploy $DASHBOARD_SERVICE \
  --image gcr.io/$PROJECT_ID/$DASHBOARD_SERVICE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

cd ..

echo "----------------------------------------"
echo "🎉 Full Deployment Complete!"

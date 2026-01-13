# Production Deployment Plan

## Goal
Deploy the latest secure codebase to production environments on Google Cloud Platform.

## User Review Required
> [!IMPORTANT]
> **Production Deployment**: This action will modify your live services.
> - **Backend**: `session-api` (Cloud Run `us-central1`)
> - **Frontend**: `admin-dashboard` (Cloud Run `us-central1`)
> - **Functions**: Firebase Cloud Functions
>
> **Pre-requisite**: The branch `fix/secure-and-update-auth` will be merged into `main`.

## Proposed Steps

### 1. Codebase Preparation
- Merge `fix/secure-and-update-auth` into `main`.
- Pull `main` to ensure local workspace is up-to-date.

### 2. Backend Deployment (`session-api`)
- **Build**: Submit build to Cloud Build.
  ```bash
  gcloud builds submit --tag gcr.io/jvc-ai-kms/session-api api/
  ```
- **Deploy**: Update Cloud Run service.
  ```bash
  gcloud run deploy session-api \
    --image gcr.io/jvc-ai-kms/session-api \
    --region us-central1 \
    --platform managed
  ```

### 3. Frontend Deployment (`admin-dashboard`)
- **Build**: Submit build using `cloudbuild.yaml` (injecting API URL).
  ```bash
  gcloud builds submit --config admin-dashboard/cloudbuild.yaml admin-dashboard/
  ```
- **Deploy**: Update Cloud Run service.
  ```bash
  gcloud run deploy admin-dashboard \
    --image gcr.io/jvc-ai-kms/admin-dashboard \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated
  ```

### 4. Firebase Functions
- **Deploy**:
  ```bash
  firebase deploy --only functions
  ```

## Verification Plan
### Automated Tests
- [ ] Check Cloud Run Service Health (Green status).
- [ ] Verify Frontend loads (`https://admin-dashboard-182206907696.us-central1.run.app` or custom domain).
- [ ] Verify Backend API health check.

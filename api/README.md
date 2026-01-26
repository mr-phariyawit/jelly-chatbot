# Jelly ChatBot API

## Configuration

The application uses environment variables for configuration. You can set them in a `.env` file for local development or in your cloud provider's secret manager.

### Key Variables

- `API_BASE_URL`: The public URL of this backend service.
- `SESSION_TIMEOUT_MINUTES`: Session duration (default: 30).
- `GCS_BUCKET_NAME`: Google Cloud Storage bucket for file uploads.
- `GEMINI_API_KEY`: API Key for Google Gemini.
- `DATABASE_URL`: **(Required for Cloud Run)** Connection string for the database.
  - Format: `postgresql://user:password@host/dbname?host=/cloudsql/project:region:instance`

## Deployment

### Cloud Run Requirements

**Important**: This application includes a **Safe Crash** mechanism to prevent data loss.

- **SQLite is blocked** on Cloud Run because the filesystem is ephemeral (files are deleted on restart).
- You **MUST** provide a `DATABASE_URL` pointing to a persistent database (e.g., Cloud SQL PostgreSQL) when deploying to Cloud Run.
- If `DATABASE_URL` is missing, the app will **crash on startup** with an error message.

### CORS & Safe Crash

If the application crashes on startup (e.g., due to missing DB config), Cloud Run will return a **503 Service Unavailable** error.

- This 503 error often lacks CORS headers.
- **Symptom**: The frontend dashboard shows **CORS Errors** in the console.
- **Fix**: Check Cloud Run logs. If you see "Production runtime requires a persistent database...", you need to configure `DATABASE_URL`.

## Local Development

For local development, you can omit `DATABASE_URL` to default to `sqlite:///./sessions.db` (created in the current directory).

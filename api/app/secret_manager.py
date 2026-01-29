"""
GCP Secret Manager Integration
Loads secrets from GCP Secret Manager with environment variable fallback.
Used in production (Cloud Run) where secrets should not be in env vars.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Cache to avoid repeated API calls
_secret_cache: dict = {}


def get_secret(secret_id: str, fallback_env: str = None, project_id: str = None) -> str:
    """
    Fetch a secret from GCP Secret Manager.
    Falls back to environment variable if Secret Manager is unavailable.

    Args:
        secret_id: The secret ID in Secret Manager (e.g., "GEMINI_API_KEY")
        fallback_env: Environment variable name to use as fallback (defaults to secret_id)
        project_id: GCP project ID (defaults to GCLOUD_PROJECT env var)

    Returns:
        The secret value as a string
    """
    if fallback_env is None:
        fallback_env = secret_id

    # Check cache first
    if secret_id in _secret_cache:
        return _secret_cache[secret_id]

    # Try Secret Manager (only in Cloud Run / production)
    if os.getenv("K_SERVICE"):
        try:
            from google.cloud import secretmanager

            project = project_id or os.getenv("GCLOUD_PROJECT", "jvc-it-support")
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project}/secrets/{secret_id}/versions/latest"

            response = client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")

            _secret_cache[secret_id] = secret_value
            logger.info(f"Loaded secret '{secret_id}' from Secret Manager")
            return secret_value

        except Exception as e:
            logger.warning(f"Secret Manager lookup failed for '{secret_id}': {e}. Falling back to env var.")

    # Fallback to environment variable
    value = os.getenv(fallback_env, "")
    if value:
        _secret_cache[secret_id] = value
    return value


def clear_cache():
    """Clear the secret cache (useful for testing)."""
    _secret_cache.clear()

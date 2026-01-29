"""
Application Configuration
Centralized configuration management using environment variables
with GCP Secret Manager support for sensitive credentials in production.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

from app.secret_manager import get_secret


class Settings:
    """Application settings loaded from environment variables and Secret Manager"""

    # API Settings
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://session-api-1088865818405.us-central1.run.app")

    # Session Settings
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

    # CORS Settings
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",

        "https://admin-dashboard-1088865818405.us-central1.run.app"
    ]

    # GCS Settings
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "jelly-chatbot-uploads")
    SERVICE_ACCOUNT_EMAIL: str = os.getenv("SERVICE_ACCOUNT_EMAIL", "1088865818405-compute@developer.gserviceaccount.com")

    # Sensitive credentials — loaded from Secret Manager in production, env vars locally
    GEMINI_API_KEY: str = get_secret("GEMINI_API_KEY")
    JIRA_API_TOKEN: str = get_secret("JIRA_API_TOKEN")
    JIRA_EMAIL: str = get_secret("JIRA_EMAIL")

    # Admin Settings
    SUPER_ADMIN_EMAILS: list = [e.strip() for e in os.getenv("SUPER_ADMIN_EMAILS", "").split(",") if e.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

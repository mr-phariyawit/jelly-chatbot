"""
Application Configuration
Centralized configuration management using environment variables
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""

    # API Settings
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://session-api-n7u6wpcbqa-uc.a.run.app")

    # Session Settings
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

    # CORS Settings
    CORS_ORIGINS: list = [
        "https://admin-dashboard-n7u6wpcbqa-uc.a.run.app",
        "https://admin-dashboard-687023036300.us-central1.run.app",
        "http://localhost:3000",
    ]

    # GCS Settings
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "jvc-ai-kms-uploads")

    # AI Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Admin Settings
    SUPER_ADMIN: str = os.getenv("SUPER_ADMIN", "")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

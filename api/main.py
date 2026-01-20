"""
Session Logging API for LINE IT Support Bot
Tracks chat sessions and messages from all users

Refactored: Modular router-based architecture
"""

import sys
import os

# Add api directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from database import init_db
from app.migrations import run_migrations
from app.config import settings

# Import routers
from app.routers import health, sessions, bots, webhooks, files, auth, analytics, chat

# Initialize FastAPI app
app = FastAPI(
    title="Session Logging API",
    description="API for tracking LINE bot chat sessions",
    version="1.2.2",
)

# CORS middleware - Robust dynamic origin validation
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.run\.app|http://localhost:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for faster response delivery
app.add_middleware(GZipMiddleware, minimum_size=500)


@app.on_event("startup")
def startup():
    """Initialize database and run migrations on startup."""
    init_db()
    run_migrations()


# Include routers
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(bots.router)
app.include_router(webhooks.router)
app.include_router(files.router)
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(chat.router)


# Migration endpoint (kept at root level for backwards compatibility)
@app.post("/debug/migrate-files-to-gcs")
def migrate_files_to_gcs():
    """Migrate legacy files with content in DB to GCS"""
    from sqlalchemy.orm import Session as DBSession
    from database import get_db, SessionLocal
    from migration_service import MigrationService

    db = SessionLocal()
    try:
        service = MigrationService(db)
        result = service.migrate_legacy_files()
        return result
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

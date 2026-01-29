"""
Session Logging API for LINE IT Support Bot
Tracks chat sessions and messages from all users

Refactored: Modular router-based architecture
"""

import sys
import os

# Add api directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize structured logging before anything else
from app.logging_config import setup_logging
setup_logging()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from slowapi.errors import RateLimitExceeded

from database import init_db
from app.migrations import run_migrations
from app.rate_limiter import limiter

# Import routers
from app.routers import health, sessions, bots, webhooks, files, auth, analytics, chat

# Initialize FastAPI app
app = FastAPI(
    title="Jelly ChatBot API",
    description="API for Jelly ChatBot multi-tenant LINE bot platform",
    version="1.3.0",
)

# Rate limiting
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )

# CORS middleware - Robust dynamic origin validation
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://admin-dashboard-1088865818405.us-central1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for faster response delivery
app.add_middleware(GZipMiddleware, minimum_size=500)

@app.get("/debug/cors")
def debug_cors():
    return {"allowed_origins": [
        "http://localhost:3000",
        "https://admin-dashboard-1088865818405.us-central1.run.app",
    ]}


import logging
logger = logging.getLogger(__name__)


@app.on_event("startup")
def startup():
    """Initialize database and run migrations on startup."""
    logger.info("Starting Jelly ChatBot API v1.3.0")
    init_db()
    run_migrations()
    logger.info("Startup complete")


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
    from database import SessionLocal
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

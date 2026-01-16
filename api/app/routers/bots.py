"""
Bots Router
Endpoints for managing LINE bot configurations
"""

import os
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from pydantic import BaseModel

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db
from models import Bot, BotLog
from schemas import (
    BotCreate,
    BotUpdate,
    BotResponse,
    BotDetailResponse,
    FileResponse,
    BotLogResponse,
    BotLogsListResponse,
)
from processor import Processor
from app.config import settings
from utils import sanitize_text

router = APIRouter(prefix="/bots", tags=["Bots"])


def log_bot_event(db: DBSession, bot_id: str, level: str, event_type: str, message: str, metadata: dict = None):
    """Helper to log bot events to database"""
    try:
        clean_message = sanitize_text(message)
        clean_metadata = None
        if metadata:
            json_str = json.dumps(metadata, ensure_ascii=False)
            clean_metadata = sanitize_text(json_str)

        log_entry = BotLog(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            level=level,
            event_type=event_type,
            message=clean_message,
            log_metadata=clean_metadata,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Failed to log bot event: {e}")


@router.post("", response_model=BotResponse)
def create_bot(
    bot: BotCreate,
    db: DBSession = Depends(get_db),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email")
):
    """Create a new LINE bot configuration"""
    bot_id = str(uuid.uuid4())
    webhook_path = f"/webhook/{bot_id[:8]}"

    # Check if webhook path already exists
    existing = db.query(Bot).filter(Bot.webhook_path == webhook_path).first()
    if existing:
        webhook_path = f"/webhook/{bot_id}"

    new_bot = Bot(
        id=bot_id,
        name=bot.name,
        description=bot.description,
        channel_id=bot.channel_id,
        channel_secret=bot.channel_secret,
        channel_access_token=bot.channel_access_token,
        user_id=x_user_email or bot.user_id,
        webhook_path=webhook_path,
        system_prompt=bot.system_prompt,
    )

    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)

    log_bot_event(db, new_bot.id, "INFO", "BOT_CREATED", f"Bot '{new_bot.name}' created", {
        "bot_name": new_bot.name,
        "created_by": x_user_email or bot.user_id
    })

    return BotResponse(
        id=new_bot.id,
        name=new_bot.name,
        description=new_bot.description,
        channel_id=new_bot.channel_id,
        webhook_path=new_bot.webhook_path,
        webhook_url=f"{settings.API_BASE_URL}{new_bot.webhook_path}",
        is_active=new_bot.is_active,
        file_count=0,
        session_count=0,
        created_at=new_bot.created_at,
    )


@router.post("/{bot_id}/generate-prompt")
def generate_bot_prompt(bot_id: str, db: DBSession = Depends(get_db)):
    """Generate a suggested system prompt based on uploaded files."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    processor = Processor()
    suggestion = processor.generate_system_prompt_suggestion(db, bot_id)

    if suggestion.startswith("Error"):
        raise HTTPException(status_code=400, detail=suggestion)

    return {"suggested_prompt": suggestion}


@router.get("", response_model=List[BotResponse])
def list_bots(
    db: DBSession = Depends(get_db),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email")
):
    """List all bots, filtered by owner or admin role"""
    from models import AdminUser

    query = db.query(Bot)

    # Check if user is super admin or has admin role
    is_admin = False
    allowed_bot_ids = None

    if x_user_email:
        if x_user_email == settings.SUPER_ADMIN:
            is_admin = True
        else:
            # Check admin_users table for role
            admin_user = db.query(AdminUser).filter(AdminUser.email == x_user_email).first()
            if admin_user and admin_user.role == "admin":
                is_admin = True
                allowed_bot_ids = admin_user.allowed_bot_ids

    # Filter bots based on access
    if not is_admin:
        # Regular users only see their own bots
        if x_user_email:
            query = query.filter(Bot.user_id == x_user_email)
    elif allowed_bot_ids:
        # Admin with restricted access
        query = query.filter(Bot.id.in_(allowed_bot_ids))
    # else: admin with full access sees all bots

    bots = query.order_by(desc(Bot.created_at)).all()

    return [
        BotResponse(
            id=b.id,
            name=b.name,
            description=b.description,
            channel_id=b.channel_id,
            webhook_path=b.webhook_path,
            webhook_url=f"{settings.API_BASE_URL}{b.webhook_path}",
            is_active=b.is_active,
            file_count=len(b.files) if b.files else 0,
            session_count=len(b.sessions) if b.sessions else 0,
            created_at=b.created_at,
        )
        for b in bots
    ]


@router.get("/{bot_id}", response_model=BotDetailResponse)
def get_bot(bot_id: str, db: DBSession = Depends(get_db)):
    """Get bot details including files"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    return BotDetailResponse(
        id=bot.id,
        name=bot.name,
        description=bot.description,
        channel_id=bot.channel_id,
        webhook_path=bot.webhook_path,
        webhook_url=f"{settings.API_BASE_URL}{bot.webhook_path}",
        is_active=bot.is_active,
        file_count=len(bot.files) if bot.files else 0,
        session_count=len(bot.sessions) if bot.sessions else 0,
        created_at=bot.created_at,
        system_prompt=bot.system_prompt,
        model_config_json=bot.model_config,
        files=[
            FileResponse(
                id=f.id,
                bot_id=f.bot_id,
                filename=f.filename,
                content_type=f.content_type,
                size_bytes=f.size_bytes,
                uploaded_at=f.uploaded_at,
                description=f.description,
            )
            for f in bot.files
        ],
    )


@router.patch("/{bot_id}", response_model=BotResponse)
def update_bot(bot_id: str, update: BotUpdate, db: DBSession = Depends(get_db)):
    """Update bot credentials or settings"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if update.name is not None:
        bot.name = update.name
    if update.description is not None:
        bot.description = update.description
    if update.channel_secret is not None:
        bot.channel_secret = update.channel_secret
    if update.channel_access_token is not None:
        bot.channel_access_token = update.channel_access_token
    if update.is_active is not None:
        bot.is_active = update.is_active
    if update.user_id is not None:
        bot.user_id = update.user_id
    if update.system_prompt is not None:
        bot.system_prompt = update.system_prompt
    if update.model_config_json is not None:
        bot.model_config = update.model_config_json

    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)

    return BotResponse(
        id=bot.id,
        name=bot.name,
        description=bot.description,
        channel_id=bot.channel_id,
        webhook_path=bot.webhook_path,
        webhook_url=f"{settings.API_BASE_URL}{bot.webhook_path}",
        is_active=bot.is_active,
        file_count=len(bot.files) if bot.files else 0,
        session_count=len(bot.sessions) if bot.sessions else 0,
        created_at=bot.created_at,
        system_prompt=bot.system_prompt,
        model_config_json=bot.model_config,
    )


@router.delete("/{bot_id}")
def delete_bot(bot_id: str, db: DBSession = Depends(get_db)):
    """Delete bot and all associated data"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    bot_name = bot.name

    log_bot_event(db, bot_id, "WARN", "BOT_DELETED", f"Bot '{bot_name}' deleted", {
        "bot_name": bot_name
    })

    db.delete(bot)
    db.commit()

    return {"message": f"Bot {bot_id} deleted successfully"}


# ===================
# Bot Logs Endpoints
# ===================

@router.get("/{bot_id}/logs", response_model=BotLogsListResponse)
def list_bot_logs(
    bot_id: str,
    level: Optional[str] = Query(None, description="Filter by level: INFO, WARN, ERROR"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: DBSession = Depends(get_db),
):
    """List technical logs for a specific bot with optional filtering"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    query = db.query(BotLog).filter(BotLog.bot_id == bot_id)

    if level:
        query = query.filter(BotLog.level == level.upper())
    if event_type:
        query = query.filter(BotLog.event_type == event_type.upper())

    total = query.count()
    logs = query.order_by(desc(BotLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return BotLogsListResponse(
        logs=[
            BotLogResponse(
                id=log.id,
                bot_id=log.bot_id,
                level=log.level,
                event_type=log.event_type,
                message=log.message,
                metadata=log.log_metadata,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{bot_id}/logs/stats")
def get_bot_log_stats(bot_id: str, db: DBSession = Depends(get_db)):
    """Get log statistics for a bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    total = db.query(BotLog).filter(BotLog.bot_id == bot_id).count()
    info_count = db.query(BotLog).filter(BotLog.bot_id == bot_id, BotLog.level == "INFO").count()
    warn_count = db.query(BotLog).filter(BotLog.bot_id == bot_id, BotLog.level == "WARN").count()
    error_count = db.query(BotLog).filter(BotLog.bot_id == bot_id, BotLog.level == "ERROR").count()

    webhook_count = db.query(BotLog).filter(BotLog.bot_id == bot_id, BotLog.event_type == "WEBHOOK").count()
    llm_count = db.query(BotLog).filter(BotLog.bot_id == bot_id, BotLog.event_type == "LLM_CALL").count()
    rag_count = db.query(BotLog).filter(BotLog.bot_id == bot_id, BotLog.event_type == "RAG_SEARCH").count()
    jira_count = db.query(BotLog).filter(BotLog.bot_id == bot_id, BotLog.event_type == "JIRA").count()

    return {
        "total": total,
        "by_level": {
            "INFO": info_count,
            "WARN": warn_count,
            "ERROR": error_count,
        },
        "by_event_type": {
            "WEBHOOK": webhook_count,
            "LLM_CALL": llm_count,
            "RAG_SEARCH": rag_count,
            "JIRA": jira_count,
        }
    }


@router.get("/{bot_id}/logs/{log_id}", response_model=BotLogResponse)
def get_bot_log(bot_id: str, log_id: str, db: DBSession = Depends(get_db)):
    """Get a single log entry detail"""
    log = db.query(BotLog).filter(BotLog.id == log_id, BotLog.bot_id == bot_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    return BotLogResponse(
        id=log.id,
        bot_id=log.bot_id,
        level=log.level,
        event_type=log.event_type,
        message=log.message,
        metadata=log.log_metadata,
        created_at=log.created_at,
    )


@router.delete("/{bot_id}/logs")
def clear_bot_logs(
    bot_id: str,
    older_than_days: int = Query(7, ge=1, description="Delete logs older than N days"),
    db: DBSession = Depends(get_db),
):
    """Clear old logs for a specific bot"""
    from datetime import timedelta

    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    deleted = db.query(BotLog).filter(
        BotLog.bot_id == bot_id,
        BotLog.created_at < cutoff
    ).delete()
    db.commit()

    return {"message": f"Deleted {deleted} logs older than {older_than_days} days"}

"""
Analytics Router
Dashboard analytics and statistics endpoints
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func, cast, Date
from pydantic import BaseModel

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db
from models import Bot, Session, Message, File, BotLog

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class AnalyticsOverview(BaseModel):
    """Overview analytics for dashboard"""
    total_messages: int = 0
    total_sessions: int = 0
    total_files: int = 0
    total_bots: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    active_users_7d: int = 0


class TokenUsageStats(BaseModel):
    """Token usage statistics"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class MessagesByDay(BaseModel):
    """Message count by day"""
    date: str
    count: int


class AnalyticsDashboard(BaseModel):
    """Full analytics dashboard response"""
    overview: AnalyticsOverview
    token_usage: TokenUsageStats
    messages_by_day: List[MessagesByDay] = []
    top_bots: List[Dict[str, Any]] = []
    recent_errors: int = 0


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    db: DBSession = Depends(get_db)
):
    """Get overview analytics for the dashboard"""
    bot_filter = Bot.id == bot_id if bot_id else True

    total_bots = db.query(func.count(Bot.id)).filter(bot_filter).scalar() or 0
    total_sessions = db.query(func.count(Session.id)).join(Bot).filter(bot_filter).scalar() or 0
    total_messages = db.query(func.count(Message.id)).join(Session).join(Bot).filter(bot_filter).scalar() or 0
    total_files = db.query(func.count(File.id)).join(Bot).filter(bot_filter).scalar() or 0

    # Token usage from logs
    total_tokens = 0
    llm_logs = db.query(BotLog).filter(
        BotLog.event_type.in_(["LLM_CALL", "TALK_TO_DATA", "AI_CALL"])
    )
    if bot_id:
        llm_logs = llm_logs.filter(BotLog.bot_id == bot_id)

    for log in llm_logs.all():
        if log.log_metadata:
            try:
                metadata = json.loads(log.log_metadata)
                if "token_usage" in metadata and metadata["token_usage"]:
                    total_tokens += metadata["token_usage"].get("total_tokens", 0)
            except json.JSONDecodeError:
                pass

    # Estimated cost (Gemini 2.0 Flash pricing: ~$0.075/1M tokens average)
    estimated_cost = (total_tokens / 1_000_000) * 0.075

    # Active users (unique sessions in last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active_users = db.query(func.count(func.distinct(Session.user_id))).filter(
        Session.started_at >= seven_days_ago
    ).scalar() or 0

    return AnalyticsOverview(
        total_messages=total_messages,
        total_sessions=total_sessions,
        total_files=total_files,
        total_bots=total_bots,
        total_tokens=total_tokens,
        estimated_cost_usd=round(estimated_cost, 4),
        active_users_7d=active_users
    )


@router.get("/token-usage", response_model=TokenUsageStats)
def get_token_usage(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    days: int = Query(30, description="Number of days to look back"),
    db: DBSession = Depends(get_db)
):
    """Get token usage statistics"""
    start_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(BotLog).filter(
        BotLog.event_type.in_(["LLM_CALL", "TALK_TO_DATA", "AI_CALL"]),
        BotLog.created_at >= start_date
    )
    if bot_id:
        query = query.filter(BotLog.bot_id == bot_id)

    prompt_tokens = 0
    completion_tokens = 0

    for log in query.all():
        if log.log_metadata:
            try:
                metadata = json.loads(log.log_metadata)
                if "token_usage" in metadata and metadata["token_usage"]:
                    prompt_tokens += metadata["token_usage"].get("prompt_tokens", 0)
                    completion_tokens += metadata["token_usage"].get("completion_tokens", 0)
            except json.JSONDecodeError:
                pass

    total = prompt_tokens + completion_tokens
    estimated_cost = (total / 1_000_000) * 0.075

    return TokenUsageStats(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total,
        estimated_cost_usd=round(estimated_cost, 4)
    )


@router.get("/messages-by-day", response_model=List[MessagesByDay])
def get_messages_by_day(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    days: int = Query(14, description="Number of days to look back"),
    db: DBSession = Depends(get_db)
):
    """Get message count by day for charts"""
    start_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(
        cast(Message.timestamp, Date).label('date'),
        func.count(Message.id).label('count')
    ).join(Session).join(Bot)

    if bot_id:
        query = query.filter(Bot.id == bot_id)

    query = query.filter(Message.timestamp >= start_date)\
                 .group_by(cast(Message.timestamp, Date))\
                 .order_by(cast(Message.timestamp, Date))

    results = []
    for row in query.all():
        results.append(MessagesByDay(
            date=row.date.isoformat() if row.date else "",
            count=row.count
        ))

    return results


@router.get("/dashboard", response_model=AnalyticsDashboard)
def get_full_analytics_dashboard(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    db: DBSession = Depends(get_db)
):
    """Get complete analytics dashboard data in one call"""
    # Get overview
    overview = get_analytics_overview(bot_id=bot_id, db=db)

    # Get token usage
    token_usage = get_token_usage(bot_id=bot_id, days=30, db=db)

    # Get messages by day
    messages_by_day = get_messages_by_day(bot_id=bot_id, days=14, db=db)

    # Top bots by message count
    top_bots = []
    if not bot_id:
        top_query = db.query(
            Bot.id,
            Bot.name,
            func.count(Message.id).label('message_count')
        ).join(Session, Session.bot_id == Bot.id)\
         .join(Message, Message.session_id == Session.id)\
         .group_by(Bot.id, Bot.name)\
         .order_by(func.count(Message.id).desc())\
         .limit(5)

        for row in top_query.all():
            top_bots.append({
                "id": row.id,
                "name": row.name,
                "message_count": row.message_count
            })

    # Recent errors (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    error_query = db.query(func.count(BotLog.id)).filter(
        BotLog.level == "ERROR",
        BotLog.created_at >= seven_days_ago
    )
    if bot_id:
        error_query = error_query.filter(BotLog.bot_id == bot_id)
    recent_errors = error_query.scalar() or 0

    return AnalyticsDashboard(
        overview=overview,
        token_usage=token_usage,
        messages_by_day=messages_by_day,
        top_bots=top_bots,
        recent_errors=recent_errors
    )

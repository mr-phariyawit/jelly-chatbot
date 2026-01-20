"""
Sessions Router
Endpoints for managing chat sessions
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db
from models import Session, Message
from schemas import (
    SessionResponse,
    SessionDetailResponse,
    AddMessageRequest,
    AddMessageResponse,
    SessionUpdate,
    MessageResponse,
)
from app.config import settings

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/messages", response_model=AddMessageResponse)
def add_message(request: AddMessageRequest, db: DBSession = Depends(get_db)):
    """
    Add a message to a session.
    Creates new session if none exists or if last message was > 30 min ago.
    """
    user_id = request.user_id
    now = datetime.utcnow()
    timeout_threshold = now - timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)

    # Find active session for this user
    session = (
        db.query(Session)
        .filter(Session.user_id == user_id)
        .filter(Session.status == "active")
        .order_by(desc(Session.started_at))
        .first()
    )

    is_new_session = False

    # Check if we need a new session
    if session:
        last_message = (
            db.query(Message)
            .filter(Message.session_id == session.id)
            .order_by(desc(Message.timestamp))
            .first()
        )

        if last_message and last_message.timestamp < timeout_threshold:
            session.status = "closed"
            session.ended_at = last_message.timestamp
            db.commit()
            session = None

    if not session:
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            bot_id=request.bot_id,
            started_at=now,
            status="active",
        )
        db.add(session)
        db.commit()
        is_new_session = True

    # Create message
    message = Message(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role=request.role,
        content=request.content,
        timestamp=now,
    )
    db.add(message)

    # Update escalation if needed
    if request.is_escalated:
        session.is_escalated = True
        if request.escalation_reason:
            session.escalation_reason = request.escalation_reason

    db.commit()

    return AddMessageResponse(
        session_id=session.id,
        message_id=message.id,
        is_new_session=is_new_session,
    )


@router.get("", response_model=List[SessionResponse])
def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_escalated: Optional[bool] = Query(None, description="Filter by escalation"),
    limit: int = Query(50, le=100, description="Max results"),
    db: DBSession = Depends(get_db),
):
    """List all sessions with optional filters."""
    query = db.query(Session)

    if user_id:
        query = query.filter(Session.user_id == user_id)
    if bot_id:
        query = query.filter(Session.bot_id == bot_id)
    if status:
        query = query.filter(Session.status == status)
    if is_escalated is not None:
        query = query.filter(Session.is_escalated == is_escalated)

    sessions = query.order_by(desc(Session.started_at)).limit(limit).all()

    return [
        SessionResponse(
            id=s.id,
            user_id=s.user_id,
            started_at=s.started_at,
            ended_at=s.ended_at,
            status=s.status,
            is_escalated=s.is_escalated,
            escalation_reason=s.escalation_reason,
            bot_id=s.bot_id,
            message_count=len(s.messages),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    """Get session details including all messages."""
    session = db.query(Session).filter(Session.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDetailResponse(
        id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        status=session.status,
        is_escalated=session.is_escalated,
        escalation_reason=session.escalation_reason,
        message_count=len(session.messages),
        messages=[
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                timestamp=m.timestamp,
            )
            for m in session.messages
        ],
    )


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    update: SessionUpdate,
    db: DBSession = Depends(get_db),
):
    """Update session status or escalation."""
    session = db.query(Session).filter(Session.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if update.status is not None:
        session.status = update.status
        if update.status == "closed":
            session.ended_at = datetime.utcnow()

    if update.is_escalated is not None:
        session.is_escalated = update.is_escalated

    if update.escalation_reason is not None:
        session.escalation_reason = update.escalation_reason

    db.commit()
    db.refresh(session)

    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        status=session.status,
        is_escalated=session.is_escalated,
        escalation_reason=session.escalation_reason,
        message_count=len(session.messages),
    )

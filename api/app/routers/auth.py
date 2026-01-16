"""
Auth Router
Admin user authentication and management
"""

import os
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from pydantic import BaseModel

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db
from models import AdminUser

router = APIRouter(tags=["Auth"])


class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth authentication"""
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: str


class AdminUserResponse(BaseModel):
    """Response model for admin user"""
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    role: str
    allowed_bot_ids: Optional[List[str]]
    created_at: Optional[str]
    last_login: Optional[str]


class AdminUserUpdate(BaseModel):
    """Request body for updating admin user"""
    name: Optional[str] = None
    role: Optional[str] = None
    allowed_bot_ids: Optional[List[str]] = None


@router.post("/auth/google", response_model=AdminUserResponse)
def google_auth(request: GoogleAuthRequest, db: DBSession = Depends(get_db)):
    """
    Authenticate via Google OAuth.
    Creates user if doesn't exist, updates last_login if exists.
    """
    user = db.query(AdminUser).filter(AdminUser.email == request.email).first()

    if user:
        user.last_login = datetime.utcnow()
        if request.name:
            user.name = request.name
        if request.avatar_url:
            user.avatar_url = request.avatar_url
        db.commit()
        db.refresh(user)
    else:
        user = AdminUser(
            id=request.google_id,
            email=request.email,
            name=request.name,
            avatar_url=request.avatar_url,
            role="admin",
            allowed_bot_ids=None,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role,
        allowed_bot_ids=json.loads(user.allowed_bot_ids) if user.allowed_bot_ids else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.get("/auth/me", response_model=AdminUserResponse)
def get_current_user(email: str = Query(..., description="User email"), db: DBSession = Depends(get_db)):
    """
    Get current user info by email.
    In production, this would use a proper auth token/session.
    """
    user = db.query(AdminUser).filter(AdminUser.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role,
        allowed_bot_ids=json.loads(user.allowed_bot_ids) if user.allowed_bot_ids else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.get("/users", response_model=List[AdminUserResponse])
def list_users(db: DBSession = Depends(get_db)):
    """List all admin users"""
    users = db.query(AdminUser).order_by(desc(AdminUser.created_at)).all()

    return [
        AdminUserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            avatar_url=u.avatar_url,
            role=u.role,
            allowed_bot_ids=json.loads(u.allowed_bot_ids) if u.allowed_bot_ids else None,
            created_at=u.created_at.isoformat() if u.created_at else None,
            last_login=u.last_login.isoformat() if u.last_login else None
        )
        for u in users
    ]


@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_user(user_id: str, update: AdminUserUpdate, db: DBSession = Depends(get_db)):
    """Update admin user role or permissions"""
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update.name is not None:
        user.name = update.name
    if update.role is not None:
        user.role = update.role
    if update.allowed_bot_ids is not None:
        user.allowed_bot_ids = json.dumps(update.allowed_bot_ids) if update.allowed_bot_ids else None

    db.commit()
    db.refresh(user)

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role,
        allowed_bot_ids=json.loads(user.allowed_bot_ids) if user.allowed_bot_ids else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: DBSession = Depends(get_db)):
    """Delete an admin user"""
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": f"User {user.email} deleted successfully"}

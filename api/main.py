"""
Session Logging API for LINE IT Support Bot
Tracks chat sessions and messages from all users
"""

from datetime import datetime, timedelta
from typing import List, Optional
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File as FastAPIFile, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc, text

from database import get_db, init_db
from models import Session, Message, Bot, File
from schemas import (
    SessionResponse,
    SessionDetailResponse,
    AddMessageRequest,
    AddMessageResponse,
    SessionUpdate,
    MessageResponse,
    BotCreate,
    BotUpdate,
    BotResponse,
    BotDetailResponse,
    FileResponse,
)

# Configuration
SESSION_TIMEOUT_MINUTES = 30

# Initialize FastAPI app
app = FastAPI(
    title="Session Logging API",
    description="API for tracking LINE bot chat sessions",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    init_db()


@app.get("/health")
def health_check(db: DBSession = Depends(get_db)):
    """Health check endpoint with DB verification."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@app.post("/messages", response_model=AddMessageResponse)
def add_message(request: AddMessageRequest, db: DBSession = Depends(get_db)):
    """
    Add a message to a session.
    Creates new session if none exists or if last message was > 30 min ago.
    """
    user_id = request.user_id
    now = datetime.utcnow()
    timeout_threshold = now - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
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
        # Get last message time
        last_message = (
            db.query(Message)
            .filter(Message.session_id == session.id)
            .order_by(desc(Message.timestamp))
            .first()
        )
        
        if last_message and last_message.timestamp < timeout_threshold:
            # Session timed out, close it and create new one
            session.status = "closed"
            session.ended_at = last_message.timestamp
            db.commit()
            session = None
    
    if not session:
        # Create new session
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
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


@app.get("/sessions", response_model=List[SessionResponse])
def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_escalated: Optional[bool] = Query(None, description="Filter by escalation"),
    limit: int = Query(50, le=100, description="Max results"),
    db: DBSession = Depends(get_db),
):
    """List all sessions with optional filters."""
    query = db.query(Session)
    
    if user_id:
        query = query.filter(Session.user_id == user_id)
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
            message_count=len(s.messages),
        )
        for s in sessions
    ]


@app.get("/sessions/{session_id}", response_model=SessionDetailResponse)
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


@app.patch("/sessions/{session_id}", response_model=SessionResponse)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ApiException
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from processor import Processor

# Initialize Processor (Single instance)
processor = Processor()

@app.post("/webhook/{bot_id_prefix}")
async def active_webhook(
    bot_id_prefix: str, 
    request: Request, # Changed to Request to get headers/body
    db: DBSession = Depends(get_db)
):
    """
    Handle incoming LINE webhook events.
    Routes events to the correct bot based on ID prefix.
    """
    # 1. Find the bot
    webhook_path = f"/webhook/{bot_id_prefix}"
    bot = db.query(Bot).filter(Bot.webhook_path == webhook_path).first()
    
    if not bot:
        # Fallback: try to match by prefix just in case
        print(f"Warning: No exact match for {webhook_path}, searching by prefix")
        raise HTTPException(status_code=404, detail="Bot not found")

    if not bot.channel_secret or not bot.channel_access_token:
        print(f"Error: Bot {bot.name} missing credentials")
        raise HTTPException(status_code=500, detail="Bot configuration error")

    # 2. Validate Signature & Parse Events
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body_str = body.decode('utf-8')

    handler = WebhookHandler(bot.channel_secret)
    configuration = Configuration(access_token=bot.channel_access_token)
    
    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 3. Process Events Manually (or use handler decorators if we refactor)
    # Since we need dynamic handlers per bot, we parse JSON manually after validation
    # or iterate through handler's result if possible. 
    # For simplicity/speed in this dynamic setup: Use JSON parsing since we already validated signature.
    
    import json
    events = json.loads(body_str).get("events", [])
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        for event in events:
            if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                user_id = event["source"]["userId"]
                reply_token = event["replyToken"]
                text_content = event["message"]["text"]
                
                # --- Session Logic ---
                # Check for active session
                session = (
                    db.query(Session)
                    .filter(Session.bot_id == bot.id)
                    .filter(Session.user_id == user_id)
                    .filter(Session.status == "active")
                    .order_by(desc(Session.started_at))
                    .first()
                )

                # Check timeout
                if session:
                    last_msg = (
                        db.query(Message)
                        .filter(Message.session_id == session.id)
                        .order_by(desc(Message.timestamp))
                        .first()
                    )
                    if last_msg and last_msg.timestamp < (datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)):
                        session.status = "closed"
                        session.ended_at = last_msg.timestamp
                        db.commit()
                        session = None
                
                # Create session if needed
                if not session:
                    session = Session(
                        id=str(uuid.uuid4()),
                        bot_id=bot.id,
                        user_id=user_id,
                        started_at=datetime.utcnow(),
                        status="active"
                    )
                    db.add(session)
                    db.commit()
                    db.refresh(session)
                
                # Log User Message
                # Get conversation history for context
                history_msgs = session.messages[-5:] if session.messages else [] # Last 5 messages
                history_context = [
                    {"role": m.role, "content": m.content} for m in history_msgs
                ]

                user_msg = Message(
                    id=str(uuid.uuid4()),
                    session_id=session.id,
                    role="user",
                    content=text_content,
                    timestamp=datetime.utcnow()
                )
                db.add(user_msg)
                db.commit()

                # --- AI Processing ---
                ai_result = processor.process_message(
                    user_id=user_id,
                    content=text_content,
                    history=history_context,
                    db=db,
                    bot_id=bot.id
                )
                reply_text = ai_result["message"]
                
                # Log AI Message
                ai_msg = Message(
                    id=str(uuid.uuid4()),
                    session_id=session.id,
                    role="assistant",
                    content=reply_text,
                    timestamp=datetime.utcnow()
                )
                db.add(ai_msg)
                
                if ai_result["should_escalate"]:
                    session.is_escalated = True
                    session.escalation_reason = "AI Detected Escalation Intent"
                
                db.commit()

                # --- Reply to User ---
                try:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text=reply_text)]
                        )
                    )
                except Exception as e:
                    print(f"Error sending reply: {e}")

    return {"status": "ok"}

import os
from fastapi import UploadFile, File as FastAPIFile


# Bot CRUD endpoints
@app.post("/bots", response_model=BotResponse)
def create_bot(bot: BotCreate, db: DBSession = Depends(get_db)):
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
        user_id=bot.user_id,
        webhook_path=webhook_path,
    )
    
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    
    # Get base URL from environment or use default
    base_url = os.getenv("API_BASE_URL", "https://session-api-687023036300.us-central1.run.app")
    
    return BotResponse(
        id=new_bot.id,
        name=new_bot.name,
        description=new_bot.description,
        channel_id=new_bot.channel_id,
        webhook_path=new_bot.webhook_path,
        webhook_url=f"{base_url}{new_bot.webhook_path}",
        is_active=new_bot.is_active,
        file_count=0,
        session_count=0,
        created_at=new_bot.created_at,
    )


@app.get("/bots", response_model=List[BotResponse])
def list_bots(db: DBSession = Depends(get_db)):
    """List all bots"""
    bots = db.query(Bot).order_by(desc(Bot.created_at)).all()
    base_url = os.getenv("API_BASE_URL", "https://session-api-687023036300.us-central1.run.app")
    
    return [
        BotResponse(
            id=b.id,
            name=b.name,
            description=b.description,
            channel_id=b.channel_id,
            webhook_path=b.webhook_path,
            webhook_url=f"{base_url}{b.webhook_path}",
            is_active=b.is_active,
            file_count=len(b.files) if b.files else 0,
            session_count=len(b.sessions) if b.sessions else 0,
            created_at=b.created_at,
        )
        for b in bots
    ]


@app.get("/bots/{bot_id}", response_model=BotDetailResponse)
def get_bot(bot_id: str, db: DBSession = Depends(get_db)):
    """Get bot details including files"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    base_url = os.getenv("API_BASE_URL", "https://session-api-687023036300.us-central1.run.app")
    
    return BotDetailResponse(
        id=bot.id,
        name=bot.name,
        description=bot.description,
        channel_id=bot.channel_id,
        webhook_path=bot.webhook_path,
        webhook_url=f"{base_url}{bot.webhook_path}",
        is_active=bot.is_active,
        file_count=len(bot.files) if bot.files else 0,
        session_count=len(bot.sessions) if bot.sessions else 0,
        created_at=bot.created_at,
        files=[
            FileResponse(
                id=f.id,
                bot_id=f.bot_id,
                filename=f.filename,
                content_type=f.content_type,
                size_bytes=f.size_bytes,
                uploaded_at=f.uploaded_at,
            )
            for f in bot.files
        ],
    )


@app.patch("/bots/{bot_id}", response_model=BotResponse)
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
    
    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)
    
    base_url = os.getenv("API_BASE_URL", "https://session-api-687023036300.us-central1.run.app")
    
    return BotResponse(
        id=bot.id,
        name=bot.name,
        description=bot.description,
        channel_id=bot.channel_id,
        webhook_path=bot.webhook_path,
        webhook_url=f"{base_url}{bot.webhook_path}",
        is_active=bot.is_active,
        file_count=len(bot.files) if bot.files else 0,
        session_count=len(bot.sessions) if bot.sessions else 0,
        created_at=bot.created_at,
    )


@app.delete("/bots/{bot_id}")
def delete_bot(bot_id: str, db: DBSession = Depends(get_db)):
    """Delete bot and all associated data"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Delete will cascade to files and update sessions
    db.delete(bot)
    db.commit()
    
    return {"message": f"Bot {bot_id} deleted successfully"}


# File management endpoints
@app.post("/bots/{bot_id}/files", response_model=FileResponse)
async def upload_file(
    bot_id: str,
    file: UploadFile = FastAPIFile(...),
    db: DBSession = Depends(get_db)
):
    """Upload a knowledge base file for a bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Read file content
    content = await file.read()
    
    # For text files, store content directly
    file_content = None
    if file.content_type and file.content_type.startswith('text/'):
        file_content = content.decode('utf-8')
    
    new_file = File(
        id=str(uuid.uuid4()),
        bot_id=bot_id,
        filename=file.filename,
        content_type=file.content_type,
        content=file_content,
        size_bytes=len(content),
    )
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    return FileResponse(
        id=new_file.id,
        bot_id=new_file.bot_id,
        filename=new_file.filename,
        content_type=new_file.content_type,
        size_bytes=new_file.size_bytes,
        uploaded_at=new_file.uploaded_at,
    )


@app.get("/bots/{bot_id}/files", response_model=List[FileResponse])
def list_files(bot_id: str, db: DBSession = Depends(get_db)):
    """List all files for a bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return [
        FileResponse(
            id=f.id,
            bot_id=f.bot_id,
            filename=f.filename,
            content_type=f.content_type,
            size_bytes=f.size_bytes,
            uploaded_at=f.uploaded_at,
        )
        for f in bot.files
    ]


@app.get("/files/{file_id}/content")
def get_file_content(file_id: str, db: DBSession = Depends(get_db)):
    """Get file content"""
    file = db.query(File).filter(File.id == file_id).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"content": file.content, "filename": file.filename}


@app.delete("/files/{file_id}")
def delete_file(file_id: str, db: DBSession = Depends(get_db)):
    """Delete a file"""
    file = db.query(File).filter(File.id == file_id).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    db.delete(file)
    db.commit()
    
    return {"message": f"File {file.filename} deleted successfully"}

"""
Webhooks Router
LINE webhook handling for incoming messages
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
    PostbackAction,
    ShowLoadingAnimationRequest,
)

from database import get_db, SessionLocal
from models import Bot, Session, Message, Feedback, BotLog
from processor import Processor
from app.config import settings
from utils import sanitize_text

router = APIRouter(tags=["Webhooks"])

# Initialize Processor (Single instance)
processor = Processor()


def log_bot_event(db: DBSession, bot_id: str, level: str, event_type: str, message: str, metadata: dict = None):
    """Helper to log bot events"""
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


def process_webhook_event_background(
    bot_id: str,
    bot_channel_access_token: str,
    event: dict
):
    """
    Background task to process LINE webhook events.
    Uses its own DB session since FastAPI's session is closed after response.
    """
    db = SessionLocal()
    try:
        configuration = Configuration(access_token=bot_channel_access_token)

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            if event.get("type") == "message":
                user_id = event["source"]["userId"]
                reply_token = event["replyToken"]
                message_type = event.get("message", {}).get("type")

                # Show typing indicator (loading animation) to user
                try:
                    line_bot_api.show_loading_animation(
                        ShowLoadingAnimationRequest(
                            chat_id=user_id,
                            loading_seconds=30  # Show for up to 30 seconds (will stop when reply is sent)
                        )
                    )
                except Exception as e:
                    print(f"Error showing loading animation: {e}")

                # Retrieve Session
                session = (
                    db.query(Session)
                    .filter(Session.bot_id == bot_id)
                    .filter(Session.user_id == user_id)
                    .filter(Session.status == "active")
                    .order_by(desc(Session.started_at))
                    .first()
                )

                # Check timeout logic
                if session:
                    last_msg = (
                        db.query(Message)
                        .filter(Message.session_id == session.id)
                        .order_by(desc(Message.timestamp))
                        .first()
                    )
                    if last_msg and last_msg.timestamp < (datetime.utcnow() - timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)):
                        session.status = "closed"
                        session.ended_at = last_msg.timestamp
                        db.commit()
                        session = None

                # Create session if needed
                if not session:
                    session = Session(
                        id=str(uuid.uuid4()),
                        bot_id=bot_id,
                        user_id=user_id,
                        started_at=datetime.utcnow(),
                        status="active"
                    )
                    db.add(session)
                    db.commit()
                    db.refresh(session)

                # Handle Content
                reply_text = "ขออภัยครับ รองรับเฉพาะข้อความและรูปภาพ"
                should_escalate = False

                if message_type == "text":
                    text_content = event["message"]["text"]

                    # Log User Message
                    user_msg = Message(
                        id=str(uuid.uuid4()),
                        session_id=session.id,
                        role="user",
                        content=text_content,
                        timestamp=datetime.utcnow()
                    )
                    db.add(user_msg)

                    # AI Processing
                    history_msgs = session.messages[-5:]
                    history_context = [{"role": m.role, "content": m.content} for m in history_msgs]

                    ai_result = processor.process_message(
                        user_id=user_id,
                        content=text_content,
                        history=history_context,
                        db=db,
                        bot_id=bot_id
                    )
                    reply_text = ai_result["message"]
                    should_escalate = ai_result["should_escalate"]

                elif message_type == "image":
                    message_id = event["message"]["id"]

                    # Log User Message (Image)
                    user_msg = Message(
                        id=str(uuid.uuid4()),
                        session_id=session.id,
                        role="user",
                        content=f"[Image Message: {message_id}]",
                        timestamp=datetime.utcnow()
                    )
                    db.add(user_msg)

                    # Get Image Content
                    try:
                        line_bot_blob_api = MessagingApiBlob(api_client)
                        content = line_bot_blob_api.get_message_content(message_id)

                        # Process Image
                        ai_result = processor.process_image(
                            user_id=user_id,
                            image_content=content,
                            db=db,
                            bot_id=bot_id
                        )
                        reply_text = ai_result["message"]
                        should_escalate = ai_result["should_escalate"]

                    except Exception as e:
                        print(f"Error getting image content: {e}")
                        reply_text = "ขออภัยครับ ไม่สามารถดาวน์โหลดรูปภาพได้"
                        should_escalate = True

                # Log AI Message
                ai_msg = Message(
                    id=str(uuid.uuid4()),
                    session_id=session.id,
                    role="assistant",
                    content=reply_text,
                    timestamp=datetime.utcnow()
                )
                db.add(ai_msg)

                if should_escalate:
                    session.is_escalated = True
                    session.escalation_reason = "AI Detected Escalation (Image/Text)"

                db.commit()

                # Reply
                try:
                    feedback_items = [
                        QuickReplyItem(
                            action=PostbackAction(
                                label="👍 Helpful",
                                data=f"action=feedback&score=1&msgId={ai_msg.id}&botId={bot_id}",
                                display_text="Helpful"
                            )
                        ),
                        QuickReplyItem(
                            action=PostbackAction(
                                label="👎 Not Helpful",
                                data=f"action=feedback&score=-1&msgId={ai_msg.id}&botId={bot_id}",
                                display_text="Not Helpful"
                            )
                        )
                    ]

                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[
                                TextMessage(
                                    text=reply_text,
                                    quick_reply=QuickReply(items=feedback_items)
                                )
                            ]
                        )
                    )
                except Exception as e:
                    print(f"Error sending reply: {e}")

            # Handle Postback (Feedback)
            elif event.get("type") == "postback":
                data = event["postback"]["data"]
                params = dict(x.split('=') for x in data.split('&'))

                if params.get("action") == "feedback":
                    try:
                        score = int(params.get("score"))
                        msg_id = params.get("msgId")
                        bot_id_param = params.get("botId")
                        user_id = event["source"]["userId"]

                        fb = Feedback(
                            id=str(uuid.uuid4()),
                            user_id=user_id,
                            message_id=msg_id,
                            bot_id=bot_id_param,
                            score=score
                        )
                        db.add(fb)
                        db.commit()

                        reply_token = event["replyToken"]
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=reply_token,
                                messages=[TextMessage(text="ขอบคุณสำหรับ feedback ครับ! 🙏")]
                            )
                        )

                    except Exception as e:
                        print(f"Feedback error: {e}")
    except Exception as e:
        print(f"Background processing error: {e}")
    finally:
        db.close()


@router.post("/webhook/{bot_id_prefix}")
async def active_webhook(
    bot_id_prefix: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db)
):
    """
    Handle incoming LINE webhook events.
    Returns 200 immediately, processes in background.
    """
    # 1. Find the bot (fast DB query)
    webhook_path = f"/webhook/{bot_id_prefix}"
    bot = db.query(Bot).filter(Bot.webhook_path == webhook_path).first()

    if not bot:
        print(f"Warning: No exact match for {webhook_path}")
        raise HTTPException(status_code=404, detail="Bot not found")

    if not bot.channel_secret or not bot.channel_access_token:
        print(f"Error: Bot {bot.name} missing credentials")
        raise HTTPException(status_code=500, detail="Bot configuration error")

    # 2. Validate Signature (fast)
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body_str = body.decode('utf-8')

    handler = WebhookHandler(bot.channel_secret)

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 3. Schedule background processing for each event
    events = json.loads(body_str).get("events", [])

    # Log webhook received
    log_bot_event(db, bot.id, "INFO", "WEBHOOK", f"Received {len(events)} event(s)", {
        "event_count": len(events),
        "event_types": [e.get("type") for e in events]
    })

    for event in events:
        background_tasks.add_task(
            process_webhook_event_background,
            bot.id,
            bot.channel_access_token,
            event
        )

    # 4. Return 200 immediately - LINE is happy!
    return {"status": "ok"}

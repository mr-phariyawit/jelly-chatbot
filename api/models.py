from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, create_engine
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def utcnow():
    """Return current UTC time as naive datetime."""
    return datetime.utcnow()

class Session(Base):
    """Chat session from one user."""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    started_at = Column(DateTime, default=utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default="active")  # active, closed
    is_escalated = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    
    bot_id = Column(String, ForeignKey("bots.id"), nullable=True)
    
    messages = relationship("Message", back_populates="session", order_by="Message.timestamp")
    bot = relationship("Bot", back_populates="sessions")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "is_escalated": self.is_escalated,
            "escalation_reason": self.escalation_reason,
            "message_count": len(self.messages) if self.messages else 0,
        }


class Message(Base):
    """Individual message within a session."""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utcnow)
    
    session = relationship("Session", back_populates="messages")
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class Bot(Base):
    """LINE Bot configuration and credentials"""
    __tablename__ = "bots"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # LINE credentials
    channel_id = Column(String, nullable=False)
    channel_secret = Column(String, nullable=False)
    channel_access_token = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    
    # Webhook
    webhook_path = Column(String, unique=True, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow)
    
    # Relationships
    files = relationship("File", back_populates="bot", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="bot")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "channel_id": self.channel_id,
            "webhook_path": self.webhook_path,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "file_count": len(self.files) if self.files else 0,
            "session_count": len(self.sessions) if self.sessions else 0,
        }


class File(Base):
    """Knowledge base files per bot"""
    __tablename__ = "files"
    
    id = Column(String, primary_key=True)
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    file_url = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=utcnow)
    
    bot = relationship("Bot", back_populates="files")
    chunks = relationship("FileChunk", back_populates="file", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "bot_id": self.bot_id,
            "filename": self.filename,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


from pgvector.sqlalchemy import Vector

class FileChunk(Base):
    """Chunks of file content with vector embeddings"""
    __tablename__ = "file_chunks"

    id = Column(String, primary_key=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # Gemini text-embedding-004 is 768 dimensions
    embedding = Column(Vector(768))

    file = relationship("File", back_populates="chunks")

class Feedback(Base):
    """User feedback for AI messages"""
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True) # Refers to assistant message
    bot_id = Column(String, ForeignKey("bots.id"), nullable=True)
    user_id = Column(String, nullable=False)
    score = Column(Integer, nullable=False) # 1 or -1
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AdminUser(Base):
    """Admin dashboard users with role-based access"""
    __tablename__ = "admin_users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(String, default="admin")  # admin, viewer
    allowed_bot_ids = Column(Text, nullable=True)  # JSON array for data governance, null = all access
    created_at = Column(DateTime, default=utcnow)
    last_login = Column(DateTime, nullable=True)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "allowed_bot_ids": json.loads(self.allowed_bot_ids) if self.allowed_bot_ids else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

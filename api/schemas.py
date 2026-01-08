from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MessageCreate(BaseModel):
    role: str  # user, assistant
    content: str


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    user_id: str


class SessionUpdate(BaseModel):
    status: Optional[str] = None
    is_escalated: Optional[bool] = None
    escalation_reason: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str
    is_escalated: bool
    escalation_reason: Optional[str] = None
    message_count: int

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []


class AddMessageRequest(BaseModel):
    user_id: str
    role: str
    content: str
    is_escalated: Optional[bool] = False
    escalation_reason: Optional[str] = None


class AddMessageResponse(BaseModel):
    session_id: str
    message_id: str
    is_new_session: bool


# Bot schemas
class BotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    channel_id: str
    channel_secret: str
    channel_access_token: str
    user_id: Optional[str] = None


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    channel_secret: Optional[str] = None
    channel_access_token: Optional[str] = None
    is_active: Optional[bool] = None


class BotResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    channel_id: str
    webhook_path: str
    webhook_url: str
    is_active: bool
    file_count: int
    session_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class BotDetailResponse(BotResponse):
    files: List['FileResponse'] = []


# File schemas
class FileResponse(BaseModel):
    id: str
    bot_id: str
    filename: str
    content_type: Optional[str]
    size_bytes: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True

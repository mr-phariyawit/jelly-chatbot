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
    bot_id: Optional[str] = None
    message_count: int

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []


class AddMessageRequest(BaseModel):
    user_id: str
    role: str
    content: str
    bot_id: Optional[str] = None
    is_escalated: Optional[bool] = False
    escalation_reason: Optional[str] = None


class AddMessageResponse(BaseModel):
    session_id: str
    message_id: str
    is_new_session: bool


class BotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    channel_id: str
    channel_secret: str
    channel_access_token: str
    user_id: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config_json: Optional[str] = None  # JSON string


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    channel_secret: Optional[str] = None
    channel_access_token: Optional[str] = None
    is_active: Optional[bool] = None
    system_prompt: Optional[str] = None
    model_config_json: Optional[str] = None  # JSON string
    user_id: Optional[str] = None


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
    system_prompt: Optional[str] = None
    model_config_json: Optional[str] = None

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
    description: Optional[str]  # Added description field
    size_bytes: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# BotLog schemas
class BotLogCreate(BaseModel):
    level: str = "INFO"  # INFO, WARN, ERROR
    event_type: str  # WEBHOOK, LLM_CALL, RAG_SEARCH, JIRA, ERROR
    message: str
    metadata: Optional[str] = None  # JSON string


class BotLogResponse(BaseModel):
    id: str
    bot_id: str
    level: str
    event_type: str
    message: str
    metadata: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BotLogsListResponse(BaseModel):
    logs: List[BotLogResponse]
    total: int
    page: int

# Signed URL schemas
class SignedUrlRequest(BaseModel):
    filename: str
    content_type: str

class SignedUrlResponse(BaseModel):
    upload_url: str
    gcs_uri: str
    file_id: str

class FileConfirmRequest(BaseModel):
    file_id: str
    gcs_uri: str
    filename: str
    content_type: str
    size_bytes: int

class FileUpdate(BaseModel):
    description: Optional[str] = None

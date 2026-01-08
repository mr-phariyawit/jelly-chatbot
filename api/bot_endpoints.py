"""
Bot Management Endpoints
"""
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

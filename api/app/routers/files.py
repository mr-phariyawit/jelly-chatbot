"""
Files Router
Endpoints for managing bot knowledge base files
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, BackgroundTasks
from sqlalchemy.orm import Session as DBSession, defer
from sqlalchemy import desc
from google.cloud import storage
from pydantic import BaseModel

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db, SessionLocal
from models import Bot, File, BotLog, Feedback
from schemas import FileResponse, FileUpdate, SignedUrlRequest, SignedUrlResponse, FileConfirmRequest
from processor import Processor
from app.config import settings
from utils import sanitize_text

router = APIRouter(tags=["Files"])


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


def process_file_background(file_id: str):
    """Background task to extract text and ingest."""
    from ingestion_service import IngestionService

    db = SessionLocal()
    try:
        print(f"Starting background processing for file {file_id}")

        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            print(f"File {file_id} not found")
            return

        file.status = "indexing"
        db.commit()

        ingestion = IngestionService()

        try:
            ingestion.process_file(db, file_id)

            file = db.query(File).filter(File.id == file_id).first()
            file.status = "indexed"
            db.commit()

            log_bot_event(db, file.bot_id, "INFO", "FILE_INDEXED", f"File '{file.filename}' indexed successfully", {
                "filename": file.filename,
                "file_id": file_id
            })
            print(f"Completed background processing for file {file_id}")

        except Exception as e:
            print(f"Ingestion failed for {file_id}: {e}")
            db.rollback()
            file = db.query(File).filter(File.id == file_id).first()
            if file:
                file.status = "failed"
                file.description = f"Failed: {str(e)}"
                db.commit()

                log_bot_event(db, file.bot_id, "ERROR", "ERROR", f"File indexing failed: {file.filename}", {
                    "filename": file.filename,
                    "file_id": file_id,
                    "error": str(e)
                })

    except Exception as e:
        print(f"Background wrapper failed for {file_id}: {e}")
    finally:
        db.close()


@router.post("/bots/{bot_id}/files/signed-url", response_model=SignedUrlResponse)
def generate_signed_url(
    bot_id: str,
    request: SignedUrlRequest,
    db: DBSession = Depends(get_db)
):
    """Generate a V4 Signed URL for direct GCS upload"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    file_id = str(uuid.uuid4())
    bucket_name = settings.GCS_BUCKET_NAME
    blob_name = f"{bot_id}/{file_id}/{request.filename}"

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Generate V4 Signed URL (PUT request, 15 minutes expiration)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=request.content_type
        )

        return SignedUrlResponse(
            upload_url=url,
            gcs_uri=f"gs://{bucket_name}/{blob_name}",
            file_id=file_id
        )

    except Exception as e:
        log_bot_event(db, bot_id, "ERROR", "ERROR", f"Failed to generate signed URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {str(e)}")


@router.post("/bots/{bot_id}/files/confirm", response_model=FileResponse)
def confirm_upload(
    bot_id: str,
    request: FileConfirmRequest,
    db: DBSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Confirm file upload and trigger ingestion"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    try:
        db_file = File(
            id=request.file_id,
            bot_id=bot_id,
            filename=request.filename,
            content_type=request.content_type,
            content="[Stored in GCS]",
            gcs_uri=request.gcs_uri,
            size_bytes=request.size_bytes,
            status="pending"
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        log_bot_event(db, bot_id, "INFO", "FILE_UPLOADED", f"File '{request.filename}' confirmation received (Signed URL)", {
            "filename": request.filename,
            "file_id": request.file_id,
            "size_bytes": request.size_bytes,
            "content_type": request.content_type,
            "gcs_uri": request.gcs_uri,
            "method": "signed_url"
        })

        if background_tasks:
            background_tasks.add_task(process_file_background, db_file.id)

        return FileResponse(
            id=db_file.id,
            bot_id=db_file.bot_id,
            filename=db_file.filename,
            description=None,
            content_type=db_file.content_type,
            size_bytes=db_file.size_bytes,
            status=db_file.status,
            uploaded_at=db_file.uploaded_at.isoformat() if db_file.uploaded_at else datetime.utcnow().isoformat()
        )

    except Exception as e:
        db.rollback()
        log_bot_event(db, bot_id, "ERROR", "ERROR", f"Failed to confirm upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm upload: {str(e)}")



@router.post("/bots/{bot_id}/files", response_model=FileResponse)
def upload_file(
    bot_id: str,
    file: UploadFile = FastAPIFile(...),
    db: DBSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Upload a file to Knowledge Base (GCS Stream -> Vector DB)"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    file_id = str(uuid.uuid4())
    bucket_name = settings.GCS_BUCKET_NAME

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        blob_name = f"{bot_id}/{file_id}/{file.filename}"
        blob = bucket.blob(blob_name)

        file.file.seek(0)
        blob.upload_from_file(file.file, content_type=file.content_type)

        gcs_uri = f"gs://{bucket_name}/{blob_name}"

        try:
            file.file.seek(0, 2)
            size_bytes = file.file.tell()
        except:
            size_bytes = 0

        db_file = File(
            id=file_id,
            bot_id=bot_id,
            filename=file.filename,
            content_type=file.content_type,
            content="[Stored in GCS]",
            gcs_uri=gcs_uri,
            size_bytes=size_bytes,
            status="pending"
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        log_bot_event(db, bot_id, "INFO", "FILE_UPLOADED", f"File '{file.filename}' uploaded to GCS", {
            "filename": file.filename,
            "file_id": file_id,
            "size_bytes": size_bytes,
            "content_type": file.content_type,
            "gcs_uri": gcs_uri
        })

        background_tasks.add_task(process_file_background, db_file.id)

        return FileResponse(
            id=db_file.id,
            bot_id=db_file.bot_id,
            filename=db_file.filename,
            description=None,
            content_type=db_file.content_type,
            size_bytes=db_file.size_bytes,
            status=db_file.status,
            uploaded_at=db_file.uploaded_at.isoformat()
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/bots/{bot_id}/files", response_model=List[FileResponse])
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
            description=f.description,
        )
        for f in bot.files
    ]


@router.get("/files/{file_id}/content")
def get_file_content(file_id: str, db: DBSession = Depends(get_db)):
    """Get file content"""
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return {"content": file.content, "filename": file.filename}


@router.patch("/files/{file_id}", response_model=FileResponse)
def update_file(file_id: str, update: FileUpdate, db: DBSession = Depends(get_db)):
    """Update file description"""
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if update.description is not None:
        file.description = update.description

    db.commit()
    db.refresh(file)

    return FileResponse(
        id=file.id,
        bot_id=file.bot_id,
        filename=file.filename,
        description=file.description,
        content_type=file.content_type,
        size_bytes=file.size_bytes,
        uploaded_at=file.uploaded_at,
    )


@router.delete("/files/{file_id}")
def delete_file(file_id: str, db: DBSession = Depends(get_db)):
    """Delete a file"""
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    filename = file.filename
    bot_id = file.bot_id

    log_bot_event(db, bot_id, "WARN", "FILE_DELETED", f"File '{filename}' deleted", {
        "filename": filename,
        "file_id": file_id
    })

    db.delete(file)
    db.commit()

    return {"message": f"File {filename} deleted successfully"}


@router.post("/files/{file_id}/analyze")
def analyze_file(file_id: str, db: DBSession = Depends(get_db)):
    """Generate AI summary for a file"""
    file = db.query(File).options(defer(File.content)).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    bot = db.query(Bot).filter(Bot.id == file.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    start_time = datetime.utcnow()
    log_bot_event(db, file.bot_id, "INFO", "LLM_CALL", f"Starting AI Analysis for file: {file.filename}")

    processor = Processor()
    suggestion = processor.generate_file_summary(db, file_id)

    if suggestion.startswith("Error"):
        log_bot_event(db, file.bot_id, "ERROR", "ERROR", f"AI Analysis Failed for {file.filename}: {suggestion}")
        raise HTTPException(status_code=400, detail=suggestion)

    file.description = suggestion
    db.commit()

    elapsed = (datetime.utcnow() - start_time).total_seconds()
    log_bot_event(db, file.bot_id, "INFO", "LLM_CALL", f"AI Analysis Success for {file.filename}", {
        "summary_preview": suggestion[:100],
        "latency_s": elapsed
    })

    return {"summary": suggestion}


@router.get("/feedbacks", response_model=List[Dict[str, Any]])
def get_feedbacks(bot_id: str = None, limit: int = 50, db: DBSession = Depends(get_db)):
    """List user feedbacks"""
    query = db.query(Feedback)

    if bot_id:
        query = query.filter(Feedback.bot_id == bot_id)

    query = query.order_by(desc(Feedback.created_at)).limit(limit)

    results = []
    for fb in query.all():
        results.append({
            "id": fb.id,
            "score": fb.score,
            "message_id": fb.message_id,
            "user_id": fb.user_id,
            "created_at": fb.created_at.isoformat()
        })
    return results

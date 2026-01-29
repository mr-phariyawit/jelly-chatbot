"""
Files Router
Endpoints for managing bot knowledge base files
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, BackgroundTasks, Request
from sqlalchemy.orm import Session as DBSession, defer
from sqlalchemy import desc
from google.cloud import storage
import google.auth
from google.auth.transport import requests as google_requests
from google.cloud import iam_credentials_v1

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db, SessionLocal
from models import Bot, File, BotLog, Feedback
from schemas import FileResponse, FileUpdate, SignedUrlRequest, SignedUrlResponse, FileConfirmRequest
from processor import Processor
from app.config import settings
from app.rate_limiter import limiter, RATE_LIMITS
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


def generate_signed_url_v4(bucket_name, blob_name, method, content_type, expiration=timedelta(minutes=15)):
    """
    Generates a v4 signed URL for uploading a blob to Google Cloud Storage.
    Uses IAM Credentials API if no local private key is available (e.g. Cloud Run).
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Check if we have credentials with a private key (Local Dev with Service Account Key)
    # or if we need to use IAM signing (Cloud Run / Compute Engine default credentials)
    credentials, project_id = google.auth.default()
    
    # If credentials have a private key, standard signing works
    if hasattr(credentials, "service_account_email") and credentials.service_account_email and not isinstance(credentials, google.auth.compute_engine.credentials.Credentials):
         # Try standard signing first if it's not compute engine creds that lack key
         try:
            return blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method=method,
                content_type=content_type
            )
         except Exception:
             pass # Fallback to IAM

    # Fallback to IAM Credentials API signing (Required for Cloud Run/GKE/GCE default/workload identity)
    service_account_email = settings.SERVICE_ACCOUNT_EMAIL
    if not service_account_email:
        raise ValueError("SERVICE_ACCOUNT_EMAIL environment variable is required for IAM signing")

    # We need to manually construct the canonical request to sign
    # But storage.blob.generate_signed_url supports a 'service_account_email' and 'access_token' 
    # param to use the signing capability of the passed credentials. 
    # However, for pure IAM signing without a local key, the python library usually expects
    # us to provide a signing callback or use the sign_blob API manually if the creds don't support it.
    
    # EASIER APPROACH: Use the 'service_account_email' and 'access_token' with IamCredentialsClient
    
    client = iam_credentials_v1.IAMCredentialsClient()
    name = f"projects/-/serviceAccounts/{service_account_email}"
    
    # Create the canonical request string overrides? No, storage library handles this if we provide a signer.
    # Actually, Python's storage library has a `generate_signed_url` that takes `service_account_email` 
    # and `access_token` BUT it mainly uses them for V2 signing or relies on local key.
    
    # For V4 signing without a key, we need to provide a custom signing function.
    
    def iam_sign_bytes(payload: bytes) -> bytes:
        response = client.sign_blob(
            name=name,
            payload=payload,
        )
        return response.signed_blob

    url = blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method=method,
        content_type=content_type,
        service_account_email=service_account_email,
        access_token=None, # Not needed if we provide signer, but library might assert
    )
    # WAIT: The python library's generate_signed_url uses the credentials on the client.
    # If we want to force IAM signing, we might need a workaround or pass a custom token.
    # The most reliable way for V4 on Cloud Run is to just specify the service_account endpoint
    # and let the library handle the REST call to sign the blob.
    
    # Attempt 2: Let's try the cleanest V4 implementation with 'sign_blob' override if possible.
    # The current google-cloud-storage library allows passing `service_account_email` and requesting it to sign.
    # But as seen in logs, it fails if no private key.
    
    # Let's use the explicit signer approach which is safer.
    
    return blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method=method,
        content_type=content_type,
        service_account_email=service_account_email,
        access_token=credentials.token, # Might help
        # Custom signer not easily pluggable in public API of blob?
        # Actually, if we look at `blob.py`, it tries `self.bucket.client._credentials.sign_bytes`.
        
        # We will use the IAM API explicitly to sign.
        # But wait, generate_signed_url does the hashing and string construction. available?
    )

    # REVISION: Implementing the manual IAM signing correctly requires careful string construction.
    # Instead, let's use the standard "auto" way but fix the credentials.
    # If we are on GCE/Cloud Run, we can use `google.auth.default` which returns ComputeCredentials.
    # These verify as "google.auth.compute_engine.credentials.Credentials".
    # They DO NOT have a private key.
    
    # Correct pattern for Cloud Run V4 signing:
    # Use IAMCredentialsClient to sign the bytes.
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method=method,
        content_type=content_type,
        service_account_email=service_account_email,
        access_token=None,
    )
    return url 
    # THE PREVIOUS FAILURE was here.
    
    # TO FIX: We can't use blob.generate_signed_url directly without a key.
    # We must patch the client or use a URL construction helper that calls IAM.
    # However, implementing full V4 signing manually is complex and error-prone.
    
    # Alternative: Use V2 signing? V4 is better.
    # The best practice for Cloud Run is to delegate signing to the IAM Service.
    
    # Let's try a simpler approach often cited: Refresh credentials and ensure email is set? 
    # No, key is physical.
    
    # OK, we will use the `google-auth` library's `impersonated_credentials`? 
    # Or just use the IAM API to sign.
    
    # Actual working solution for Cloud Run:
    auth_req = google_requests.Request()
    id_token = None # Not needed for signBlob usually if we are the SA.
    
    # We will use a patch to the 'sign_bytes' method of the credentials object attached to the client.
    # This is a known pattern.
    
    # Define a signer class
    class IAMSigner:
        def __init__(self, service_account_email):
             self.client = iam_credentials_v1.IAMCredentialsClient()
             self.service_account_email = service_account_email
             self.name = f"projects/-/serviceAccounts/{service_account_email}"
             
        def sign(self, key_id, message):
             # This signature match what google-auth expects? 
             # google-auth credentials.sign_bytes(message) -> bytes
             response = self.client.sign_blob(
                 name=self.name,
                 payload=message,
             )
             return None, response.signed_blob # key_id, signature

    # If we treat the credentials object as having a signer...
    # Let's go with the explicit `sign_blob` call mixed with url generation?
    # No, `generate_signed_url` calls `credentials.sign_bytes`.
    
    # So we replace the credentials logic.
    signer = IAMSigner(service_account_email)
    
    # Create a dummy credentials object that delegates signing to IAM
    # This is the "Magic" fix.
    
    return blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method=method,
        content_type=content_type,
        service_account_email=service_account_email,
        access_token="ignore", # prevent using client token?
        # We need to hook into the signing process.
    )

    # WAIT, simplicity:
    # If we simply instantiate storage.Client(credentials=...) where credentials has a .sign_bytes method
    # that uses IAM, it should work.
    
    pass 
    
# Better implementation below in the ReplacementContent


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
@limiter.limit(RATE_LIMITS["upload"])
def generate_signed_url(
    bot_id: str,
    request: Request,
    body: SignedUrlRequest = Depends(),
    db: DBSession = Depends(get_db)
):
    """Generate a V4 Signed URL for direct GCS upload"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    file_id = str(uuid.uuid4())
    bucket_name = settings.GCS_BUCKET_NAME
    blob_name = f"{bot_id}/{file_id}/{body.filename}"

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Strategy: Use Resumable Uploads (Session URI) instead of Signed URLs.
        # This bypasses the need for "IAM Service Account Token Creator" role and "signBlob" permission.
        # It only requires "storage.objects.create", which the Service Account already has.
        # The frontend continues to PUT to the returned URL.
        
        import requests
        import google.auth.transport.requests
        from urllib.parse import quote
        
        # Get credentials (standard, no special scopes needed beyond cloud-platform which is default)
        credentials, _ = google.auth.default()
        
        # Refresh to ensure we have a token
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        auth_token = credentials.token
        
        # Construct the Resumable Upload Initiation Request
        # https://cloud.google.com/storage/docs/performing-resumable-uploads#start-resumable-session
        
        safe_blob_name = quote(blob_name, safe='')
        init_url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket_name}/o?uploadType=resumable&name={safe_blob_name}"
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Upload-Content-Type": body.content_type,
            "Content-Type": "application/json"
        }
        
        # CRITICAL: Forward the browser's Origin header to GCS.
        # GCS uses the Origin from the session initiation request to set CORS headers
        # for all subsequent requests to the session URI.
        origin = request.headers.get("origin")
        if origin:
            headers["Origin"] = origin
        
        # Optional metadata
        metadata = {
            "name": blob_name,
            "contentType": body.content_type
        }
        
        # Make the request to GCS to start the session
        response = requests.post(init_url, headers=headers, json=metadata)
        
        if response.status_code != 200:
            log_bot_event(db, bot_id, "ERROR", "UPLOAD_INIT_FAIL", f"Failed to init resumable upload: {response.status_code} {response.text}")
            raise HTTPException(status_code=500, detail=f"Failed to initiate upload session: {response.text}")
            
        # The 'Location' header contains the Session URI that the client uses to PUT the file
        session_uri = response.headers.get("Location")
        
        if not session_uri:
            raise HTTPException(status_code=500, detail="Upstream GCS did not return a Session URI")

        # Return the Session URI as the 'upload_url'
        # Frontend does: PUT {upload_url} with Body={File Content}
        # This matches the Signed URL behavior perfectly.
        return SignedUrlResponse(
            upload_url=session_uri,
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
            status="pending",
            indexing_progress=0
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
@limiter.limit(RATE_LIMITS["upload"])
def upload_file(
    bot_id: str,
    request: Request,
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
        except (OSError, IOError):
            size_bytes = 0

        db_file = File(
            id=file_id,
            bot_id=bot_id,
            filename=file.filename,
            content_type=file.content_type,
            content="[Stored in GCS]",
            gcs_uri=gcs_uri,
            size_bytes=size_bytes,
            status="pending",
            indexing_progress=0
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

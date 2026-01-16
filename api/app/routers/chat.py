"""
Chat Router
"Talk to Data" endpoint for testing bot RAG pipeline
"""

import os
import time
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db
from models import Bot, BotLog, FileChunk, File as DBFile
from processor import Processor
from utils import sanitize_text

router = APIRouter(tags=["Chat"])


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


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    debug: bool = False


class ChatSource(BaseModel):
    """Source citation for RAG"""
    filename: str
    chunk_preview: str
    similarity_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    message: str
    sources: List[ChatSource] = []
    debug_info: Optional[Dict[str, Any]] = None
    token_usage: Optional[Dict[str, int]] = None


@router.post("/bots/{bot_id}/chat", response_model=ChatResponse)
def chat_with_bot(
    bot_id: str,
    request: ChatRequest,
    db: DBSession = Depends(get_db)
):
    """
    Talk to Data: Test bot with RAG pipeline from admin dashboard.
    Mirrors LINE webhook logic but returns JSON for debugging.
    """
    start_time = time.time()

    # 1. Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # 2. Initialize processor
    processor_instance = Processor()
    if not processor_instance.gemini:
        raise HTTPException(status_code=500, detail="AI not configured (missing GEMINI_API_KEY)")

    # 3. Build system prompt
    system_prompt = bot.system_prompt or "You are a helpful AI assistant."

    # 4. RAG: Search knowledge base for relevant chunks
    sources = []
    debug_chunks = []
    rag_context = ""

    try:
        # Embed query
        query_vector = processor_instance.gemini.embed_content(request.message, "retrieval_query")

        # Vector search
        chunks = db.query(FileChunk).join(DBFile).filter(DBFile.bot_id == bot_id)\
                   .order_by(FileChunk.embedding.cosine_distance(query_vector))\
                   .limit(5).all()

        if chunks:
            rag_parts = []
            for i, chunk in enumerate(chunks):
                rag_parts.append(f"--- Context {i+1} (from {chunk.file.filename}) ---\n{chunk.content}")
                sources.append(ChatSource(
                    filename=chunk.file.filename,
                    chunk_preview=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                ))
                if request.debug:
                    debug_chunks.append({
                        "index": i+1,
                        "filename": chunk.file.filename,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content[:500],
                        "length": len(chunk.content)
                    })
            rag_context = "\n\n".join(rag_parts)

    except Exception as e:
        rag_context = ""
        if request.debug:
            debug_chunks = [{"error": str(e)}]

    # 5. Build final prompt
    final_prompt = f"""
    {system_prompt}

    === Knowledge Base Context ===
    {rag_context if rag_context else "(No relevant context found)"}

    === User Question ===
    {request.message}

    === Instructions ===
    - Answer the user's question based on the context provided.
    - If the context is empty or irrelevant, answer based on your general knowledge but indicate that.
    - Respond in Thai unless the user explicitly asks for English.
    """

    # 6. Generate response
    try:
        response_text = processor_instance.gemini.generate_content(final_prompt, timeout=60)
        token_usage = getattr(processor_instance.gemini, 'last_token_usage', None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    # 7. Log the chat event
    latency_ms = int((time.time() - start_time) * 1000)
    log_bot_event(db, bot_id, "INFO", "TALK_TO_DATA", f"Admin chat test: '{request.message[:50]}...'", {
        "query_preview": request.message[:100],
        "chunks_found": len(sources),
        "latency_ms": latency_ms,
        "token_usage": token_usage
    })

    # 8. Build response
    response = ChatResponse(
        message=response_text,
        sources=sources,
        token_usage=token_usage
    )

    if request.debug:
        response.debug_info = {
            "system_prompt_preview": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
            "chunks_retrieved": debug_chunks,
            "latency_ms": latency_ms,
            "model": processor_instance.gemini.model if processor_instance.gemini else None
        }

    return response

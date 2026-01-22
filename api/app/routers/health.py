"""
Health & Debug Router
Endpoints for health checks, testing, and debugging
"""

import os
import time
import requests
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import text, desc

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db, migrate_db
from models import Bot, FileChunk, File as FileModel
from processor import Processor

router = APIRouter(tags=["Health & Debug"])


@router.get("/")
def root():
    """Root endpoint to avoid 404."""
    return {
        "service": "Jelly ChatBot API",
        "status": "running",
        "docs_url": "/docs",
        "health_check": "/health"
    }


@router.get("/health")
def health_check(db: DBSession = Depends(get_db)):
    """Health check endpoint with DB verification."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@router.get("/echo")
def echo(msg: str = "hello"):
    """Simple echo test - no external calls."""
    return {"echo": msg, "timestamp": datetime.utcnow().isoformat()}


@router.post("/debug/migrate")
def manual_migrate(db: DBSession = Depends(get_db)):
    """Trigger DB migration manually."""
    try:
        migrate_db()
        return {"status": "migration completed"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@router.get("/test-gemini")
def test_gemini():
    """Test Gemini API using REST (not gRPC SDK)."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return {"status": "fail", "error": "GEMINI_API_KEY not set"}

    try:
        start = time.time()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": "Say 'สวัสดี' (Hello in Thai)"}]}]
        }

        response = requests.post(url, json=payload, timeout=30)
        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            text_response = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {
                "status": "pass",
                "time_ms": round(elapsed, 2),
                "model": "gemini-2.0-flash",
                "response": text_response[:100]
            }
        else:
            return {"status": "fail", "error": response.text[:200]}

    except Exception as e:
        return {"status": "fail", "error": str(e)}


@router.get("/test-processor")
def test_processor(message: str = "สวัสดี"):
    """Test processor without database (no RAG)."""
    import traceback

    try:
        start = time.time()
        p = Processor()

        result = p.process_message(
            user_id="test-user",
            content=message,
            history=[],
            db=None,
            bot_id=None
        )
        elapsed = (time.time() - start) * 1000

        return {
            "status": "pass",
            "time_ms": round(elapsed, 2),
            "response": result.get("message", "")[:300],
            "should_escalate": result.get("should_escalate", False)
        }
    except Exception as e:
        return {"status": "fail", "error": str(e), "traceback": traceback.format_exc()}


@router.get("/test-bot/{bot_id}")
def test_bot(bot_id: str, message: str = "สวัสดี ทดสอบระบบ", db: DBSession = Depends(get_db)):
    """
    Test bot processing without LINE webhook.
    Tests: DB, Gemini API, Vector Search, Full Processing Flow.
    """
    import google.generativeai as genai

    results = {
        "bot_id": bot_id,
        "test_message": message,
        "tests": {},
        "ai_response": None,
        "total_time_ms": 0
    }
    start_total = time.time()

    # Test 1: Database & Bot Lookup
    try:
        start = time.time()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        elapsed = (time.time() - start) * 1000

        if bot:
            results["tests"]["database"] = {"status": "pass", "time_ms": round(elapsed, 2), "bot_name": bot.name}
        else:
            bot = db.query(Bot).filter(Bot.webhook_path.contains(bot_id[:8])).first()
            if bot:
                results["tests"]["database"] = {"status": "pass", "time_ms": round(elapsed, 2), "bot_name": bot.name, "matched_by": "prefix"}
                bot_id = bot.id
            else:
                results["tests"]["database"] = {"status": "fail", "error": "Bot not found"}
                return results
    except Exception as e:
        results["tests"]["database"] = {"status": "fail", "error": str(e)}
        return results

    # Test 2: Gemini API Connection
    try:
        start = time.time()
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Say 'API OK' in 2 words")
        elapsed = (time.time() - start) * 1000

        results["tests"]["gemini_api"] = {
            "status": "pass",
            "time_ms": round(elapsed, 2),
            "model": "gemini-2.0-flash",
            "test_response": response.text[:50] if response.text else "empty"
        }
    except Exception as e:
        results["tests"]["gemini_api"] = {"status": "fail", "error": str(e)}
        return results

    # Test 3: Vector Search
    try:
        start = time.time()
        chunk_count = db.query(FileChunk).join(FileModel).filter(FileModel.bot_id == bot_id).count()
        elapsed = (time.time() - start) * 1000

        results["tests"]["vector_search"] = {
            "status": "pass",
            "time_ms": round(elapsed, 2),
            "chunks_available": chunk_count
        }
    except Exception as e:
        results["tests"]["vector_search"] = {"status": "skip", "reason": str(e)}

    # Test 4: Full Processing Flow
    try:
        start = time.time()
        test_processor = Processor()
        ai_result = test_processor.process_message(
            user_id="test-user-001",
            content=message,
            history=[],
            db=db,
            bot_id=bot_id
        )
        elapsed = (time.time() - start) * 1000

        results["tests"]["full_processing"] = {
            "status": "pass",
            "time_ms": round(elapsed, 2)
        }
        results["ai_response"] = ai_result.get("message", "")[:500]
        results["should_escalate"] = ai_result.get("should_escalate", False)

    except Exception as e:
        results["tests"]["full_processing"] = {"status": "fail", "error": str(e)}

    results["total_time_ms"] = round((time.time() - start_total) * 1000, 2)
    results["overall_status"] = "pass" if all(
        t.get("status") in ["pass", "skip"] for t in results["tests"].values()
    ) else "fail"

    return results

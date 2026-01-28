"""
Debug script to check file indexing status and vector chunks.
Usage: python scripts/debug_file_indexing.py [bot_name_pattern]
"""
import os
import sys

# Add api path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api'))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Bot, File, FileChunk, BotLog

# Load DATABASE_URL from env or .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def debug_bot_files(bot_name_pattern: str = "PaPa"):
    print(f"\n🔍 Searching for bot matching: '{bot_name_pattern}'\n")
    
    # Find bot
    bot = db.query(Bot).filter(Bot.name.ilike(f"%{bot_name_pattern}%")).first()
    if not bot:
        print(f"❌ Bot not found matching '{bot_name_pattern}'")
        all_bots = db.query(Bot.name, Bot.id).all()
        print("Available bots:")
        for name, id in all_bots:
            print(f"  - {name} ({id})")
        return
    
    print(f"✅ Found Bot: {bot.name}")
    print(f"   ID: {bot.id}")
    print(f"   Active: {bot.is_active}")
    
    # List files
    files = db.query(File).filter(File.bot_id == bot.id).all()
    print(f"\n📁 Files ({len(files)} total):\n")
    
    for f in files:
        # Count chunks
        chunk_count = db.query(func.count(FileChunk.id)).filter(FileChunk.file_id == f.id).scalar()
        
        # Status indicator
        status_icon = {
            "indexed": "✅",
            "pending": "⏳",
            "processing": "🔄",
            "indexing": "🔄",
            "failed": "❌",
            "extracted": "📝"
        }.get(f.status, "❓")
        
        print(f"  {status_icon} {f.filename}")
        print(f"     Status: {f.status}")
        print(f"     Progress: {f.indexing_progress}%")
        print(f"     Chunks: {chunk_count}")
        print(f"     GCS URI: {f.gcs_uri or 'None'}")
        print(f"     Content Type: {f.content_type}")
        if f.description:
            print(f"     Description: {f.description[:100]}...")
        print()
    
    # Check for recent errors in logs
    print("\n📋 Recent Bot Logs (last 10):\n")
    logs = db.query(BotLog).filter(
        BotLog.bot_id == bot.id
    ).order_by(BotLog.created_at.desc()).limit(10).all()
    
    for log in logs:
        level_icon = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌"}.get(log.level, "📝")
        print(f"  {level_icon} [{log.created_at}] {log.event_type}: {log.message[:80]}")
        if log.log_metadata:
            print(f"     Metadata: {log.log_metadata[:100]}...")

if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "PaPa"
    debug_bot_files(pattern)

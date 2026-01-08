
import os
import logging
from database import SessionLocal
from models import Bot, File
from processor import Processor

# Setup logging
logging.basicConfig(level=logging.INFO)

db = SessionLocal()
bot = db.query(Bot).filter(Bot.channel_id == "2008690282").first()

if bot:
    print(f"Bot Found: {bot.id}")
    
    # Check File
    file = db.query(File).filter(File.bot_id == bot.id).first()
    if file:
        print(f"File Found: {file.filename} (Size: {len(file.content)} chars)")
        print(f"Content Preview: {file.content[:50]}...")
    else:
        print("No files found via direct DB query")

    # Check Processor Logic
    proc = Processor()
    kb = proc._fetch_knowledge_base(db, bot.id)
    print("\n--- Processor Retrieval Result ---")
    print(kb)
    print("----------------------------------")
else:
    print("Bot not found")

db.close()

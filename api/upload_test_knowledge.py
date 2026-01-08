
from database import SessionLocal
from models import File, Bot
import uuid
import datetime

db = SessionLocal()
bot = db.query(Bot).filter(Bot.channel_id == "2008690282").first()

if bot:
    # Check if file already exists
    existing = db.query(File).filter(File.bot_id == bot.id, File.filename == "wifi_config.txt").first()
    if not existing:
        print("Uploading Test Knowledge File...")
        new_file = File(
            id=str(uuid.uuid4()),
            bot_id=bot.id,
            filename="wifi_config.txt",
            content_type="text/plain",
            content="JVC Office WiFi Password: 8888-8888\nPrinter IP: 192.168.1.100", # Secret Info
            size_bytes=100,
            uploaded_at=datetime.datetime.utcnow()
        )
        db.add(new_file)
        db.commit()
        print("File Uploaded!")
    else:
        print("Test File already exists.")
else:
    print("Bot not found! Run create_test_bot.py first.")

db.close()

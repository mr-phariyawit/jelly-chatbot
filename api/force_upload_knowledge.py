
from database import SessionLocal
from models import File, Bot
import uuid
import datetime

TARGET_BOT_ID = "bc807ae7-0615-4790-8eed-f65ebc4c0bdc"

db = SessionLocal()
bot = db.query(Bot).filter(Bot.id == TARGET_BOT_ID).first()

if bot:
    print(f"Uploading to Bot: {bot.name} ({bot.id})")
    
    # Clean existing
    db.query(File).filter(File.bot_id == bot.id).delete()
    
    new_file = File(
        id=str(uuid.uuid4()),
        bot_id=bot.id,
        filename="office_info.txt",
        content_type="text/plain",
        content="JVC Office Location: 24th Floor, Spring Tower, Phayathai. Open: 09:00 - 18:00.\nReception Phone: 02-123-4567",
        size_bytes=100,
        uploaded_at=datetime.datetime.utcnow()
    )
    db.add(new_file)
    db.commit()
    print("File Uploaded Successfully to Target Bot!")
else:
    print("Target Bot NOT FOUND!")

db.close()

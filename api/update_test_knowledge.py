
from database import SessionLocal
from models import File, Bot

db = SessionLocal()
files = db.query(File).filter(File.filename == "wifi_config.txt").all()
for f in files:
    f.filename = "office_info.txt"
    f.content = "JVC Office Location: 24th Floor, Spring Tower, Phayathai. Open: 09:00 - 18:00.\nReception Phone: 02-123-4567"
    db.add(f)
db.commit()
print("Updated knowledge file to 'office_info.txt'")
db.close()

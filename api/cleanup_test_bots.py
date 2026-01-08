
import os
import sys

# Add the current directory to sys.path to ensure modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Bot

def cleanup_bots():
    db = SessionLocal()
    try:
        # Delete bots created by Playwright (Name starts with "Playwright Bot")
        bots_to_delete = db.query(Bot).filter(Bot.name.like("Playwright Bot%")).all()
        count = len(bots_to_delete)
        for bot in bots_to_delete:
            db.delete(bot)
        db.commit()
        print(f"Deleted {count} Playwright test bots.")
    except Exception as e:
        print(f"Error cleaning up bots: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_bots()

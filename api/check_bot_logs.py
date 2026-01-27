"""
Script to check bot logs and configuration in DB
"""
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import text # Import text explicitly

# Add api directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Bot

def check_bot_data():
    session = SessionLocal()
    try:
        # 1. List all bots
        print("===== BOTS =====")
        bots = session.query(Bot).all()
        for bot in bots:
            print(f"ID: {bot.id}")
            print(f"Name: {bot.name}")
            print(f"Webhook Path: {bot.webhook_path}")
            print(f"Trigger Names: {bot.trigger_names}")
            print(f"Model Config: {bot.model_config}")
            print("-" * 20)

        # 2. Check recent logs (last 1 hour)
        print("\n===== RECENT BOT LOGS (Last 1 Hour) =====")
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        # Use simple text query to avoid model dependency issues if schema mismatched
        logs = session.execute(text(
            "SELECT event_type, message, created_at, log_metadata FROM bot_logs "
            "WHERE created_at > :since ORDER BY created_at DESC LIMIT 20"
        ), {"since": one_hour_ago}).fetchall()
        
        if not logs:
            print("No logs found in the last hour.")
        
        for log in logs:
            print(f"[{log.created_at}] {log.event_type}: {log.message}")
            if log.log_metadata:
                print(f"   Metadata: {log.log_metadata}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_bot_data()

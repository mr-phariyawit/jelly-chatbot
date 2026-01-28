"""
Debug script to check file indexing status via Production API.
Usage: python scripts/debug_file_indexing_api.py [bot_name_pattern]
"""
import requests
import sys
import json

API_URL = "https://session-api-1088865818405.us-central1.run.app"

def debug_bot_files(bot_name_pattern: str = "PaPa"):
    print(f"\n🔍 Connecting to {API_URL}...")
    print(f"   Looking for bot matching: '{bot_name_pattern}'\n")
    
    # 1. List Bots
    try:
        resp = requests.get(f"{API_URL}/bots")
        resp.raise_for_status()
        bots = resp.json()
        print(f"✅ Found {len(bots)} bots.\n")
    except Exception as e:
        print(f"❌ Failed to list bots: {e}")
        return

    # 2. Find Target Bot
    target_bot = None
    for bot in bots:
        if bot_name_pattern.lower() in bot['name'].lower():
            target_bot = bot
            break
            
    if not target_bot:
        print(f"❌ Bot matching '{bot_name_pattern}' not found.")
        print("Available bots:")
        for b in bots:
            print(f"  - {b['name']} (ID: {b['id']})")
        return

    print(f"✅ Found Bot: {target_bot['name']}")
    print(f"   ID: {target_bot['id']}")
    print(f"   Active: {target_bot.get('is_active', 'N/A')}")
    print(f"   File Count: {target_bot.get('file_count', 'N/A')}")
    
    # 3. Get Files for this Bot
    try:
        files_resp = requests.get(f"{API_URL}/bots/{target_bot['id']}/files")
        files_resp.raise_for_status()
        files = files_resp.json()
        print(f"\n📁 Files ({len(files)} total):\n")
        
        for f in files:
            # Status indicator
            status_icon = {
                "indexed": "✅",
                "pending": "⏳",
                "processing": "🔄", 
                "indexing": "🔄",
                "failed": "❌",
                "extracted": "📝"
            }.get(f.get('status', ''), "❓")
            
            print(f"  {status_icon} {f['filename']}")
            print(f"     ID: {f['id']}")
            print(f"     Status: {f.get('status', 'N/A')}")
            print(f"     Content Type: {f.get('content_type', 'N/A')}")
            print(f"     Size: {f.get('size_bytes', 0)} bytes")
            if f.get('description'):
                print(f"     Description: {f['description'][:100]}...")
            print()
            
    except Exception as e:
        print(f"❌ Failed to get files: {e}")
    
    # 4. Get Bot Logs (check for errors)
    print("\n📋 Recent Bot Logs (last 20):\n")
    try:
        logs_resp = requests.get(f"{API_URL}/bots/{target_bot['id']}/logs?page_size=20")
        logs_resp.raise_for_status()
        logs = logs_resp.json().get('logs', [])
        
        for log in logs:
            level_icon = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌"}.get(log.get('level', ''), "📝")
            print(f"  {level_icon} [{log.get('created_at', '')}] {log.get('event_type', '')}: {log.get('message', '')[:80]}")
            if log.get('metadata'):
                meta_str = str(log['metadata'])[:100]
                print(f"     Metadata: {meta_str}...")
    except Exception as e:
        print(f"❌ Failed to fetch logs: {e}")
    
    # 5. Check Health/Counts (if endpoint exists)
    print("\n🏥 Checking Vector DB Status...")
    try:
        health_resp = requests.get(f"{API_URL}/bots/{target_bot['id']}/health")
        health_resp.raise_for_status()
        health = health_resp.json()
        print(f"   Chunks indexed: {health.get('chunk_count', 'N/A')}")
        print(f"   Status: {health.get('status', 'N/A')}")
    except Exception as e:
        print(f"   ⚠️ Health endpoint not available or failed: {e}")

if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "PaPa"
    debug_bot_files(pattern)

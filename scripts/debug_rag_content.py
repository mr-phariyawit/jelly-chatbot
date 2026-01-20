import requests
import json
import sys

API_URL = "https://session-api-n7u6wpcbqa-uc.a.run.app"

def debug_rag():
    print(f"🔍 Connecting to {API_URL}...")
    
    # 1. List Bots
    try:
        resp = requests.get(f"{API_URL}/bots")
        resp.raise_for_status()
        bots = resp.json()
        print(f"✅ Found {len(bots)} bots.")
    except Exception as e:
        print(f"❌ Failed to list bots: {e}")
        return

    # 2. Find Target Bot
    target_bot = None
    for bot in bots:
        if "Line Integration Test Bot" in bot['name'] or "LINE Integration" in bot['name']:
            target_bot = bot
            break
            
    if not target_bot:
        print("❌ 'LINE Integration Test Bot' not found.")
        # Debug: list all names
        print("Available bots:", [b['name'] for b in bots])
        return

    print(f"✅ Found Bot: {target_bot['name']} (ID: {target_bot['id']})")
    
    # 3. Chat with Debug Mode
    query = "explain workflow with mermaidchart"
    print(f"❓ Sending query: '{query}'...")
    
    try:
        chat_resp = requests.post(
            f"{API_URL}/bots/{target_bot['id']}/chat",
            json={"message": query, "debug": True}
        )
        chat_resp.raise_for_status()
        result = chat_resp.json()
        
        print("\n🤖 Bot Response:", result['message'])
        
        print("\n📄 Sources:")
        for source in result.get('sources', []):
            print(f"- {source['filename']}")
            print(f"  Preview: {source['chunk_preview'][:100]}...")
            
        print("\n🔍 Debug Info:")
        debug_info = result.get('debug_info', {})
        chunks = debug_info.get('chunks_retrieved', [])
        print(f"  Chunks Retrieved: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"\n  [Chunk {i+1}] Score: {chunk.get('score', 'N/A')}")
            print(f"  Content: {chunk.get('content', '')[:500]}...") # Print first 500 chars
            
    except Exception as e:
        print(f"❌ Chat failed: {e}")

    # 4. Fetch Logs
    print("\n📋 Fetching Bot Logs...")
    try:
        log_resp = requests.get(f"{API_URL}/bots/{target_bot['id']}/logs?page_size=20")
        log_resp.raise_for_status()
        logs = log_resp.json()['logs']
        for log in logs:
            print(f"[{log['created_at']}] [{log['level']}] {log['event_type']}: {log['message']}")
            if log.get('metadata'):
                print(f"   Metadata: {log['metadata']}")
    except Exception as e:
        print(f"❌ Failed to fetch logs: {e}")

if __name__ == "__main__":
    debug_rag()

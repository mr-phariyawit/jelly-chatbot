import requests
import json
import time

# Configuration
SOURCE_API_URL = "https://session-api-687023036300.us-central1.run.app"
DEST_API_URL = "https://session-api-1088865818405.us-central1.run.app"
API_TIMEOUT = 30

def get_bots(api_url):
    """Fetch all bots from API"""
    try:
        # Assuming listing bots requires X-User-Email header for admin access if implemented, 
        # or it might be public if not secured (based on router code, it checks header).
        # We might need to ask user for their email if this returns 403/empty.
        headers = {"X-User-Email": "mr.phariyawit@gmail.com"} 
        response = requests.get(f"{api_url}/bots", headers=headers, timeout=API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch bots from {api_url}: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching bots from {api_url}: {e}")
        return []

def create_bot(api_url, bot_data):
    """Create a bot in the destination API"""
    try:
        # Map fields from response to creation schema
        payload = {
            "name": bot_data["name"],
            "description": bot_data.get("description"),
            "channel_id": bot_data["channel_id"],
            "channel_secret": "PLACEHOLDER_SECRET", # Retrieving secret might not be possible from public list
            "channel_access_token": "PLACEHOLDER_TOKEN",
            "user_id": "mr.phariyawit@gmail.com", # Assign to admin
            "system_prompt": bot_data.get("system_prompt"),
            "trigger_names": bot_data.get("trigger_names"),
            "is_active": bot_data.get("is_active", True)
        }
        
        headers = {"X-User-Email": "mr.phariyawit@gmail.com"}
        response = requests.post(f"{api_url}/bots", json=payload, headers=headers, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            print(f"✅ Created bot: {bot_data['name']}")
            return response.json()
        elif response.status_code == 409:
             print(f"⚠️ Bot might already exist: {bot_data['name']}")
        else:
            print(f"❌ Failed to create bot {bot_data['name']}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating bot: {e}")
        return None

def main():
    print("🚀 Starting Data Migration...")
    print(f"Source: {SOURCE_API_URL}")
    print(f"Dest:   {DEST_API_URL}")
    
    # 1. Migrate Bots
    print("\n--- Migrating Bots ---")
    bots = get_bots(SOURCE_API_URL)
    print(f"Found {len(bots)} bots in source.")
    
    for bot in bots:
        create_bot(DEST_API_URL, bot)
        time.sleep(1) # Rate limit safety

if __name__ == "__main__":
    main()

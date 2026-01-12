
import requests
import json

API_URL = "https://session-api-182206907696.us-central1.run.app"
USER_ID = "U4bc18b6ecbdc3f7984b2e249d16c854f"

def check_response():
    # List sessions for user
    resp = requests.get(f"{API_URL}/sessions", params={"user_id": USER_ID, "limit": 1})
    if resp.status_code != 200:
        print(f"Error fetching sessions: {resp.text}")
        return

    sessions = resp.json()
    if not sessions:
        print("No sessions found.")
        return

    latest_session = sessions[0]
    session_id = latest_session['id']
    print(f"Checking Session ID: {session_id}")

    # Get details
    detail_resp = requests.get(f"{API_URL}/sessions/{session_id}")
    if detail_resp.status_code != 200:
        print("Error details")
        return
        
    messages = detail_resp.json()['messages']
    if not messages:
        print("No messages.")
        return

    last_msg = messages[-1]
    print(f"Last Role: {last_msg['role']}")
    print(f"Last Content:\n{last_msg['content']}")
    
    if "SUPER_SECRET_RESET_CODE_9999" in last_msg['content']:
        print("\n✅ SUCCESS: RAG retrieved the secret code!")
    else:
        print("\n❌ FAILURE: Secret code not found in response.")

if __name__ == "__main__":
    check_response()

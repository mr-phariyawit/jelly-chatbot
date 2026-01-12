
import hashlib
import hmac
import base64
import json
import requests
import datetime

CHANNEL_SECRET = "test_secret"
WEBHOOK_URL = "http://localhost:8000/webhook/2008690282"
USER_ID = "U1234567890abcdef1234567890abcdef"

body = {
    "destination": "Udeadbeefdeadbeefdeadbeefdeadbeef",
    "events": [
        {
            "type": "message",
            "message": {
                "type": "text",
                "id": "325708",
                "text": "What is the secret server reset code?"
            },
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            "source": {
                "type": "user",
                "userId": USER_ID
            },
            "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
            "mode": "active",
            "webhookEventId": "01FZ74A0TDDPYRVKNK77XKC3ZR",
            "deliveryContext": {
                "isRedelivery": False
            }
        }
    ]
}

body_str = json.dumps(body)

hash = hmac.new(
    CHANNEL_SECRET.encode('utf-8'),
    body_str.encode('utf-8'),
    hashlib.sha256
).digest()
signature = base64.b64encode(hash).decode('utf-8')

print(f"Sending Webhook to {WEBHOOK_URL}...")
headers = {
    'Content-Type': 'application/json',
    'X-Line-Signature': signature
}

try:
    response = requests.post(WEBHOOK_URL, headers=headers, data=body_str)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

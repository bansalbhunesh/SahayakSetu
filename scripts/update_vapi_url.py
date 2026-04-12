import os
import requests
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = "bd9bb2ff-9b1d-4f6a-86a2-11dfda391550"
RENDER_URL = "https://sahayaksetu-backend-3kxl.onrender.com/vapi-webhook"

headers = {
    'Authorization': f'Bearer {VAPI_API_KEY}',
    'Content-Type': 'application/json'
}

data = {
    'serverUrl': RENDER_URL
}

print(f"🎙️ Updating Vapi Assistant {ASSISTANT_ID}...")
print(f"🌐 Setting Server URL to: {RENDER_URL}")

response = requests.patch(f'https://api.vapi.ai/assistant/{ASSISTANT_ID}', headers=headers, json=data)

if response.status_code == 200:
    print("✅ Vapi Assistant updated successfully!")
else:
    print(f"❌ Failed to update assistant: {response.text}")

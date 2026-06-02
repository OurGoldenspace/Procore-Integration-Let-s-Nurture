import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("PROCORE_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROCORE_CLIENT_SECRET")
BASE_URL      = os.getenv("PROCORE_BASE_URL")

def get_token():
    print(f"Client ID: {CLIENT_ID[:8]}...")
    
    response = requests.post(
        "https://app.procore.com/oauth/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept":        "application/json"
        },
        data={
            "grant_type":    "client_credentials",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ Auth successful")
        print(f"Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Auth failed: {response.json()}")
        return None

if __name__ == "__main__":
    get_token()
# save as user_token_auth.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL      = os.getenv("PROCORE_BASE_URL", "https://us02.procore.com")
CLIENT_ID     = os.getenv("PROCORE_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROCORE_CLIENT_SECRET")
ACCESS_TOKEN  = os.getenv("PROCORE_ACCESS_TOKEN")

def get_token():
    """
    Tries multiple auth methods in order:
    1. Personal access token (if set in .env)
    2. Client credentials (when Prathmesh shares app credentials)
    """
    
    # Method 1 — Personal access token
    if ACCESS_TOKEN:
        print("✅ Using personal access token")
        return ACCESS_TOKEN
    
    # Method 2 — Client credentials
    if CLIENT_ID and CLIENT_SECRET:
        print(f"Client ID: {CLIENT_ID[:8]}...")
        
        # Try production URL first
        for oauth_url in [
            "https://login.procore.com/oauth/token",
            "https://app.procore.com/oauth/token",
            "https://login-sandbox.procore.com/oauth/token"
        ]:
            r = requests.post(
                f"{oauth_url}",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type":    "client_credentials",
                    "client_id":     CLIENT_ID,
                    "client_secret": CLIENT_SECRET
                }
            )
            if r.status_code == 200:
                token = r.json().get("access_token")
                print(f"✅ Auth successful via {oauth_url}")
                return token
        
        print("❌ All OAuth URLs failed")
        return None
    
    print("❌ No credentials configured in .env")
    return None

if __name__ == "__main__":
    token = get_token()
    if token:
        print(f"Token: {token[:20]}...")
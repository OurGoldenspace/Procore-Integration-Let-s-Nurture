import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("PROCORE_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROCORE_CLIENT_SECRET")
BASE_URL = os.getenv("PROCORE_BASE_URL")

def debug_token():
    # Step 1 — get token
    token_response = requests.post(
        f"{BASE_URL}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )
    
    print(f"Token response status: {token_response.status_code}")
    print(f"Full token response: {token_response.json()}")
    
    if token_response.status_code != 200:
        print("Token generation failed")
        return
    
    token_data = token_response.json()
    token = token_data.get("access_token")
    
    # Step 2 — check what scopes the token has
    print(f"\nToken scopes: {token_data.get('scope', 'not shown')}")
    print(f"Token type: {token_data.get('token_type')}")
    print(f"Expires in: {token_data.get('expires_in')} seconds")
    
    # Step 3 — try /me endpoint
    me_response = requests.get(
        f"{BASE_URL}/rest/v1.0/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"\n/me status: {me_response.status_code}")
    print(f"/me response: {me_response.json()}")
    
    # Step 4 — try companies with full debug
    companies_response = requests.get(
        f"{BASE_URL}/rest/v1.0/companies",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    print(f"\n/companies status: {companies_response.status_code}")
    print(f"/companies response: {companies_response.json()}")

if __name__ == "__main__":
    debug_token()
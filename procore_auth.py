import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("PROCORE_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROCORE_CLIENT_SECRET")
OAUTH_URL     = "https://login-sandbox.procore.com"
BASE_URL      = "https://sandbox.procore.com"

def get_token():
    print(f"Client ID: {CLIENT_ID[:8]}...")
    print(f"OAUTH URL: {OAUTH_URL}\n")
    
    # Method 1 — standard form body
    print("Trying Method 1 — form body...")
    r1 = requests.post(
        f"{OAUTH_URL}/oauth/token",
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
    print(f"Status: {r1.status_code}")
    if r1.status_code == 200:
        token = r1.json().get("access_token")
        print(f"✅ Success — Token: {token[:20]}...")
        return token
    print(f"Failed: {r1.json()}\n")

    # Method 2 — Basic Auth header
    print("Trying Method 2 — Basic Auth...")
    r2 = requests.post(
        f"{OAUTH_URL}/oauth/token",
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"}
    )
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        token = r2.json().get("access_token")
        print(f"✅ Success — Token: {token[:20]}...")
        return token
    print(f"Failed: {r2.json()}\n")

    # Method 3 — URL encoded Basic Auth
    print("Trying Method 3 — Encoded Basic Auth...")
    credentials = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode()
    
    r3 = requests.post(
        f"{OAUTH_URL}/oauth/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type":  "application/x-www-form-urlencoded",
            "Accept":        "application/json"
        },
        data={"grant_type": "client_credentials"}
    )
    print(f"Status: {r3.status_code}")
    if r3.status_code == 200:
        token = r3.json().get("access_token")
        print(f"✅ Success — Token: {token[:20]}...")
        return token
    print(f"Failed: {r3.json()}\n")

    # Method 4 — production login URL
    print("Trying Method 4 — Production login URL...")
    r4 = requests.post(
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
    print(f"Status: {r4.status_code}")
    if r4.status_code == 200:
        token = r4.json().get("access_token")
        print(f"✅ Success — Token: {token[:20]}...")
        return token
    print(f"Failed: {r4.json()}\n")

    print("❌ All methods failed")
    print("\nNext step: Check app type on developers.procore.com")
    print("Must be Service Account — not User Level")
    return None

if __name__ == "__main__":
    get_token()
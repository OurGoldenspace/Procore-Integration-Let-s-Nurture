# save as instant_test.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("PROCORE_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROCORE_CLIENT_SECRET")

# Step 1 — get fresh token
print("Getting fresh token...")
r = requests.post(
    "https://login-sandbox.procore.com/oauth/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
)

if r.status_code != 200:
    print(f"❌ Auth failed: {r.json()}")
    exit()

token = r.json().get("access_token")
print(f"✅ Token: {token[:20]}...")

# Step 2 — immediately use it
print("\nImmediately calling /companies...")
r2 = requests.get(
    "https://sandbox.procore.com/rest/v1.0/companies",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }
)
print(f"Status: {r2.status_code}")
print(f"Response: {r2.text[:300]}")

# Step 3 — try AGCM production
print("\nImmediately calling AGCM production...")
r3 = requests.get(
    "https://us02.procore.com/rest/v1.0/companies",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }
)
print(f"Status: {r3.status_code}")
print(f"Response: {r3.text[:300]}")
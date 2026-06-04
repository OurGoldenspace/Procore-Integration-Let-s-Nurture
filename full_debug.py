import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("PROCORE_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROCORE_CLIENT_SECRET")

print("=" * 50)
print("CREDENTIAL DIAGNOSTICS")
print("=" * 50)

# Check 1 — credential format
print("\n[CHECK 1] Credential format...")
print(f"Client ID:     '{CLIENT_ID}'")
print(f"Client ID length: {len(CLIENT_ID) if CLIENT_ID else 0}")
print(f"Client Secret length: {len(CLIENT_SECRET) if CLIENT_SECRET else 0}")

if CLIENT_ID and '"' in CLIENT_ID:
    print("❌ Client ID has quotes — remove them from .env")
if CLIENT_ID and ' ' in CLIENT_ID:
    print("❌ Client ID has spaces — remove them from .env")
if CLIENT_SECRET and '"' in CLIENT_SECRET:
    print("❌ Client Secret has quotes — remove them from .env")

# Check 2 — try all URLs with detailed error
print("\n[CHECK 2] Testing all OAuth endpoints...")

configs = [
    {
        "label":  "Production login",
        "url":    "https://login.procore.com/oauth/token",
        "id":     CLIENT_ID,
        "secret": CLIENT_SECRET
    },
    {
        "label":  "App.procore",
        "url":    "https://app.procore.com/oauth/token",
        "id":     CLIENT_ID,
        "secret": CLIENT_SECRET
    },
    {
        "label":  "Sandbox login",
        "url":    "https://login-sandbox.procore.com/oauth/token",
        "id":     CLIENT_ID,
        "secret": CLIENT_SECRET
    },
    {
        "label":  "US02 direct",
        "url":    "https://us02.procore.com/oauth/token",
        "id":     CLIENT_ID,
        "secret": CLIENT_SECRET
    }
]

working = None
for config in configs:
    print(f"\n  Trying {config['label']}...")
    
    # Method A — form body
    r = requests.post(
        config["url"],
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type":    "client_credentials",
            "client_id":     config["id"],
            "client_secret": config["secret"]
        }
    )
    
    if r.status_code == 200:
        token = r.json().get("access_token")
        scope = r.json().get("scope")
        print(f"  ✅ WORKS with form body")
        print(f"  Token: {token[:20]}...")
        print(f"  Scope: {scope}")
        working = config["url"]
        break
    
    # Method B — Basic Auth
    r2 = requests.post(
        config["url"],
        auth=(config["id"], config["secret"]),
        data={"grant_type": "client_credentials"}
    )
    
    if r2.status_code == 200:
        token = r2.json().get("access_token")
        print(f"  ✅ WORKS with Basic Auth")
        print(f"  Token: {token[:20]}...")
        working = config["url"]
        break
    
    print(f"  ❌ Both methods failed: {r.json().get('error_description', '')[:60]}")

# Summary
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
if working:
    print(f"✅ Working URL: {working}")
    print(f"\nUpdate .env:")
    print(f"PROCORE_OAUTH_URL={working.replace('/oauth/token', '')}")
else:
    print("❌ No URL worked")
    print("\nMost likely causes:")
    print("1. App not promoted — go to developers.procore.com")
    print("   → Open app → look for Promote button")
    print("2. Wrong grant type — must be Client Credentials")
    print("3. Try resetting Client Secret and copy fresh")
    print("4. Wait 15 min if rate limited then retry")
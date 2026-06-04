# save as raw_test.py
import requests

CLIENT_ID     = "paste_full_client_id_here"
CLIENT_SECRET = "paste_full_client_secret_here"

urls = [
    "https://login.procore.com/oauth/token",
    "https://app.procore.com/oauth/token",
    "https://login-sandbox.procore.com/oauth/token",
    "https://us02.procore.com/oauth/token"
]

for url in urls:
    print(f"\nTrying: {url}")
    r = requests.post(
        url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type":    "client_credentials",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ WORKS — use this URL")
        print(f"Token: {r.json().get('access_token')[:20]}...")
        break
    else:
        print(f"❌ {r.json()}")


print(f"Client ID length:     {len(CLIENT_ID)}")
print(f"Client Secret length: {len(CLIENT_SECRET)}")
print(f"Client ID:     '{CLIENT_ID}'")
print(f"Client Secret: '{CLIENT_SECRET[:5]}...{CLIENT_SECRET[-5:]}'")
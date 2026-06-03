# save as raw_test.py
import requests

# Paste your exact values here
CLIENT_ID     = "DZaPPl739ZOyq79PaEqnFtqHtLgs55PRJX6o4Dwnw_o"
CLIENT_SECRET = "n-zuwUnph-kEwE0c_2ppoUAcZ35ALVyVkK3pBDaF1Z0"

for url in [
    "https://app.procore.com/oauth/token",
    "https://login-sandbox.procore.com/oauth/token"
]:
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
    print(f"Response: {r.json()}")
    if r.status_code == 200:
        print("✅ THIS URL WORKS — use this in .env")
        break
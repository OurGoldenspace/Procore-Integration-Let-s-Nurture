# save as check_token_scope.py
import requests
import json
import base64
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

def check_scope():
    token = get_token()
    if not token:
        return
    
    # Decode token to see scope
    try:
        parts   = token.split(".")
        padding = parts[1] + "=" * (4 - len(parts[1]) % 4)
        decoded = json.loads(base64.b64decode(padding))
        print(f"\nToken scope: {decoded.get('scope', 'NONE')}")
        print(f"User ID:     {decoded.get('uid', 'none')}")
        print(f"App ID:      {decoded.get('aid', 'unknown')}")
    except Exception as e:
        print(f"Could not decode: {e}")
    
    # Try sandbox API directly
    print("\nTesting sandbox API...")
    r = requests.get(
        "https://sandbox.procore.com/rest/v1.0/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")

if __name__ == "__main__":
    check_scope()
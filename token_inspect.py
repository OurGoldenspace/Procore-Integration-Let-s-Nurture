# save as token_inspect.py
import requests
import os
import json
import base64
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

def inspect_token():
    token = get_token()
    if not token:
        return
    
    # Decode JWT payload without verification
    # JWT = header.payload.signature
    try:
        parts = token.split(".")
        # Add padding if needed
        payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
        decoded = json.loads(base64.b64decode(payload))
        
        print("\n=== Token Contents ===")
        for k, v in decoded.items():
            print(f"  {k}: {v}")
        
        print(f"\nScope: {decoded.get('scope', 'none')}")
        print(f"User ID: {decoded.get('uid', 'none — service account')}")
        print(f"App ID: {decoded.get('aid', 'unknown')}")
        
    except Exception as e:
        print(f"Could not decode: {e}")
    
    # Try /me with full debug
    print("\n=== Testing /me endpoint ===")
    r = requests.get(
        "https://sandbox.procore.com/rest/v1.0/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json"
        }
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:300]}")
    
    # Try vapid endpoint instead
    print("\n=== Testing /vapid/me endpoint ===")
    r2 = requests.get(
        "https://sandbox.procore.com/vapid/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json"
        }
    )
    print(f"Status: {r2.status_code}")
    print(f"Response: {r2.text[:300]}")

if __name__ == "__main__":
    inspect_token()
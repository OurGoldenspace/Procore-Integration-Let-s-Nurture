# save as decode_token.py
import requests
import json
import base64
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

token = get_token()
if not token:
    exit()

# Decode JWT
try:
    parts   = token.split(".")
    padding = parts[1] + "=" * (4 - len(parts[1]) % 4)
    decoded = json.loads(base64.b64decode(padding))
    
    print("\n=== Token Contents ===")
    for k, v in decoded.items():
        print(f"  {k}: {v}")
    
    print(f"\nScope: {decoded.get('scope', 'NONE — no permissions')}")
    print(f"UID:   {decoded.get('uid', 'None — service account')}")
    
except Exception as e:
    print(f"Decode error: {e}")
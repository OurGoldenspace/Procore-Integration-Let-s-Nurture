# save as check_env.py
import os
from dotenv import load_dotenv

load_dotenv()

client_id     = os.getenv("PROCORE_CLIENT_ID")
client_secret = os.getenv("PROCORE_CLIENT_SECRET")
oauth_url     = os.getenv("PROCORE_OAUTH_URL")
base_url      = os.getenv("PROCORE_BASE_URL")

print("=== .env Check ===")
print(f"CLIENT_ID     : '{client_id}'")
print(f"CLIENT_SECRET : '{client_secret[:5]}...{client_secret[-5:]}'" if client_secret else "NOT FOUND")
print(f"OAUTH_URL     : '{oauth_url}'")
print(f"BASE_URL      : '{base_url}'")

# Check for common issues
if client_id and ('"' in client_id or "'" in client_id):
    print("\n⚠️  CLIENT_ID has quotes — remove them from .env")
if client_secret and ('"' in client_secret or "'" in client_secret):
    print("\n⚠️  CLIENT_SECRET has quotes — remove them from .env")
if client_id and ' ' in client_id:
    print("\n⚠️  CLIENT_ID has spaces — remove them from .env")
if client_secret and ' ' in client_secret:
    print("\n⚠️  CLIENT_SECRET has spaces — remove them from .env")
# Run this to see exact field names returned by Procore
import requests, os, json
from dotenv import load_dotenv
load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL", "https://us02.procore.com")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

# reuse procore_auth
import sys
sys.path.insert(0, '.')
from procore_auth import get_token

token = get_token()
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Procore-Company-Id": str(COMPANY_ID)
}
params = {"project_id": PROJECT_ID, "company_id": COMPANY_ID}

print("=== OWNER INVOICE FIELDS ===")
r = requests.get(f"{BASE_URL}/rest/v1.0/payment_applications", headers=headers, params=params)
if r.status_code == 200:
    inv = r.json()[0]
    print(json.dumps(inv, indent=2))

print("\n=== SUBCONTRACTOR INVOICE FIELDS ===")
r = requests.get(f"{BASE_URL}/rest/v1.0/requisitions", headers=headers, params=params)
if r.status_code == 200:
    inv = r.json()[0]
    print(json.dumps(inv, indent=2))
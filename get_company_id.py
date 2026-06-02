import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL = os.getenv("PROCORE_BASE_URL")

def get_company_id():
    token = get_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/rest/v1.0/companies",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        companies = response.json()
        if isinstance(companies, list):
            for c in companies:
                if isinstance(c, dict):
                    print(f"\n✅ Company: {c.get('name')}")
                    print(f"   ID: {c.get('id')}")
                    print(f"\n→ Add to .env: PROCORE_COMPANY_ID={c.get('id')}")
        else:
            print(f"Unexpected format: {companies}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text[:200]}")

if __name__ == "__main__":
    get_company_id()
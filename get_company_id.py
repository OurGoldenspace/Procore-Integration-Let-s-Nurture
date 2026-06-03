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
        "Authorization":       f"Bearer {token}",
        "Content-Type":        "application/json",
        "Procore-Api-Version": "v1.0"
    }
    
    # Try multiple endpoints — production vs sandbox differ
    endpoints = [
        f"{BASE_URL}/rest/v1.0/companies",
        f"{BASE_URL}/rest/v1.1/companies",
        f"{BASE_URL}/vapid/companies"
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying: {endpoint}")
        r = requests.get(endpoint, headers=headers)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            companies = r.json()
            if isinstance(companies, list):
                for c in companies:
                    if isinstance(c, dict):
                        print(f"\n✅ Company: {c.get('name')}")
                        print(f"   ID: {c.get('id')}")
                        print(f"\n→ Add to .env: PROCORE_COMPANY_ID={c.get('id')}")
                return
            elif isinstance(companies, dict):
                print(f"Response: {companies}")
                return
        elif r.status_code == 403:
            print("403 — App owner restriction, need AGCM credentials")
            break
        else:
            print(f"Failed: {r.text[:100]}")
    
    print("\n❌ Could not retrieve companies")
    print("Likely need AGCM credentials from Prathmesh")

if __name__ == "__main__":
    get_company_id()
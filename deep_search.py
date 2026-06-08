# save as deep_search.py
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

def deep_search():
    token = get_token()
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": COMPANY_ID
    }
    
    endpoints = [
        # Direct costs variations
        f"/rest/v1.0/projects/{PROJECT_ID}/direct_costs",
        f"/rest/v1.0/projects/{PROJECT_ID}/direct_cost_items",
        
        # Invoice management tool
        f"/rest/v1.0/projects/{PROJECT_ID}/invoicing/invoices",
        f"/rest/v1.0/projects/{PROJECT_ID}/invoicing",
        
        # Prime contract invoices
        f"/rest/v1.0/projects/{PROJECT_ID}/prime_contracts",
        f"/rest/v1.0/projects/{PROJECT_ID}/prime_contract",
        
        # Progress billings
        f"/rest/v1.0/projects/{PROJECT_ID}/progress_billings",
        
        # Company level search
        f"/rest/v1.0/companies/{COMPANY_ID}/invoices",
        f"/rest/v1.0/companies/{COMPANY_ID}/direct_costs",
        
        # Generic project tools
        f"/rest/v1.0/projects/{PROJECT_ID}/vendors",
        f"/rest/v1.0/projects/{PROJECT_ID}/line_items",
    ]
    
    print(f"Deep searching project {PROJECT_ID}...\n")
    
    for endpoint in endpoints:
        r = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params={"company_id": COMPANY_ID}
        )
        status = r.status_code
        
        if status == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else "dict"
            print(f"✅ {endpoint}")
            print(f"   Records: {count}")
            if isinstance(data, list) and data:
                print(f"   Sample: {str(data[0])[:150]}")
            print()
        elif status == 403:
            print(f"🔒 {endpoint} — Permission denied")
        elif status == 404:
            print(f"❌ {endpoint} — Not found")
        else:
            print(f"⚠️  {endpoint} — Status {status}")

if __name__ == "__main__":
    deep_search()
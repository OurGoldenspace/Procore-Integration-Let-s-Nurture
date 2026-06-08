# save as find_invoices.py
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

def find_invoices():
    token = get_token()
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": COMPANY_ID
    }
    
    endpoints = [
        # Owner invoices
        f"/rest/v1.0/projects/{PROJECT_ID}/invoices/owners",
        f"/rest/v1.0/projects/{PROJECT_ID}/owner_invoices",
        
        # Subcontractor invoices
        f"/rest/v1.0/projects/{PROJECT_ID}/invoices/subcontractors",
        f"/rest/v1.0/projects/{PROJECT_ID}/subcontractor_invoices",
        
        # Generic invoicing
        f"/rest/v1.0/projects/{PROJECT_ID}/invoices",
        f"/rest/v1.1/projects/{PROJECT_ID}/invoices",
        
        # Billing periods
        f"/rest/v1.0/projects/{PROJECT_ID}/billing_periods",
    ]
    
    print(f"Searching invoices in project {PROJECT_ID}...\n")
    
    for endpoint in endpoints:
        r = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params={"company_id": COMPANY_ID}
        )
        print(f"Trying: {endpoint}")
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 1
            print(f"✅ FOUND {count} records")
            if isinstance(data, list) and data:
                for item in data[:3]:
                    print(f"   - #{item.get('number') or item.get('id')} | "
                          f"Status: {item.get('status')} | "
                          f"Amount: ${item.get('gross_amount') or item.get('grand_total')}")
            print(f"\n→ CORRECT ENDPOINT: {endpoint}\n")
        elif r.status_code == 403:
            print(f"🔒 Permission denied\n")
        else:
            print(f"❌ Not found\n")

if __name__ == "__main__":
    find_invoices()
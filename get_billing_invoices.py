# save as get_billing_invoices.py
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL          = os.getenv("PROCORE_BASE_URL")
COMPANY_ID        = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID        = os.getenv("PROCORE_PROJECT_ID")
BILLING_PERIOD_ID = "562949955488890"

def get_billing_invoices():
    token = get_token()
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": COMPANY_ID
    }
    
    # Try all invoice endpoints within billing period
    endpoints = [
        # Owner invoices within billing period
        f"/rest/v1.0/projects/{PROJECT_ID}/billing_periods/{BILLING_PERIOD_ID}/payment_applications",
        f"/rest/v1.0/projects/{PROJECT_ID}/billing_periods/{BILLING_PERIOD_ID}/invoices",
        f"/rest/v1.0/projects/{PROJECT_ID}/billing_periods/{BILLING_PERIOD_ID}/owner_invoices",
        
        # Subcontractor invoices within billing period
        f"/rest/v1.0/projects/{PROJECT_ID}/billing_periods/{BILLING_PERIOD_ID}/requisitions",
        f"/rest/v1.0/projects/{PROJECT_ID}/billing_periods/{BILLING_PERIOD_ID}/subcontractor_invoices",
        
        # Payment applications
        f"/rest/v1.0/projects/{PROJECT_ID}/payment_applications",
        f"/rest/v1.0/payment_applications?project_id={PROJECT_ID}",
        
        # Requisitions with billing period
        f"/rest/v1.0/requisitions?project_id={PROJECT_ID}&billing_period_id={BILLING_PERIOD_ID}",
        f"/rest/v1.0/requisitions?project_id={PROJECT_ID}",
    ]
    
    print(f"Billing Period ID: {BILLING_PERIOD_ID}\n")
    
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
                    print(f"   - ID: {item.get('id')} | "
                          f"Status: {item.get('status')} | "
                          f"Amount: ${item.get('gross_amount') or item.get('grand_total') or item.get('net_amount')}")
            elif isinstance(data, dict):
                print(f"   Response: {str(data)[:200]}")
            print(f"\n→ CORRECT ENDPOINT: {endpoint}\n")
        elif r.status_code == 403:
            print(f"🔒 Permission denied\n")
        else:
            print(f"❌ {r.text[:80]}\n")

if __name__ == "__main__":
    get_billing_invoices()
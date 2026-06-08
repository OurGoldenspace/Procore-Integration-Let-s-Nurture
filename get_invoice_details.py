# save as get_invoice_details.py
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

def get_full_details():
    token = get_token()
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": COMPANY_ID
    }
    
    params = {"company_id": COMPANY_ID, "project_id": PROJECT_ID}
    
    # Owner invoice
    print("=== OWNER INVOICE ===")
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/payment_applications/562949954671030",
        headers=headers,
        params=params
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        inv = r.json()
        print(f"All fields:")
        for k, v in inv.items():
            print(f"  {k}: {v}")
    else:
        print(f"❌ {r.text[:200]}")
    
    # Subcontractor invoices
    print("\n=== SUBCONTRACTOR INVOICES ===")
    for inv_id in ["562949960831819", "562949960831823"]:
        r = requests.get(
            f"{BASE_URL}/rest/v1.0/requisitions/{inv_id}",
            headers=headers,
            params=params
        )
        print(f"\nInvoice {inv_id} — Status: {r.status_code}")
        if r.status_code == 200:
            inv = r.json()
            print(f"All fields:")
            for k, v in inv.items():
                print(f"  {k}: {v}")
        else:
            print(f"❌ {r.text[:200]}")

if __name__ == "__main__":
    get_full_details()
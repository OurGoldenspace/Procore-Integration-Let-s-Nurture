import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

def get_invoices():
    token = get_token()
    if not token:
        return
    
    if not COMPANY_ID or not PROJECT_ID:
        print("❌ Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID in .env first")
        return
    
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(COMPANY_ID)
    }
    
    # Try owner invoices
    print("Checking owner invoices...")
    r1 = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}/invoices",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    
    print(f"Status: {r1.status_code}")
    
    if r1.status_code == 200:
        invoices = r1.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("invoices", [])
        
        if not invoices:
            print("⚠️  No invoices found — add one to the test project")
            return
        
        print(f"\n✅ Invoices found: {len(invoices)}")
        for inv in invoices:
            print(f"\n  Number: {inv.get('number')}")
            print(f"  ID:     {inv.get('id')}")
            print(f"  Status: {inv.get('status')}")
            print(f"  Total:  ${inv.get('grand_total')}")
            print(f"  → Add to .env: PROCORE_INVOICE_ID={inv.get('id')}")
    else:
        print(f"❌ Error: {r1.status_code} — {r1.text[:200]}")

if __name__ == "__main__":
    get_invoices()
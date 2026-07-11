# get_invoice_id.py
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL", "https://us02.procore.com")
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

    params = {"project_id": PROJECT_ID, "company_id": COMPANY_ID}

    all_invoices = []

    # Owner invoices
    print("Checking owner invoices (payment_applications)...")
    r1 = requests.get(
        f"{BASE_URL}/rest/v1.0/payment_applications",
        headers=headers,
        params=params
    )
    print(f"Status: {r1.status_code}")
    if r1.status_code == 200:
        items = r1.json()
        if isinstance(items, list):
            for inv in items:
                inv["_type"] = "owner"
            all_invoices.extend(items)
            print(f"✅ Found {len(items)} owner invoice(s)")
    else:
        print(f"❌ Error: {r1.text[:200]}")

    # Subcontractor invoices
    print("\nChecking subcontractor invoices (requisitions)...")
    r2 = requests.get(
        f"{BASE_URL}/rest/v1.0/requisitions",
        headers=headers,
        params=params
    )
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        items = r2.json()
        if isinstance(items, list):
            for inv in items:
                inv["_type"] = "subcontractor"
            all_invoices.extend(items)
            print(f"✅ Found {len(items)} subcontractor invoice(s)")
    else:
        print(f"❌ Error: {r2.text[:200]}")

    if not all_invoices:
        print("\n⚠️  No invoices found in either endpoint")
        return

    print(f"\n{'='*50}")
    print(f"ALL INVOICES ({len(all_invoices)} total)")
    print(f"{'='*50}")
    for inv in all_invoices:
        print(f"\n  Type:    {inv.get('_type')}")
        print(f"  ID:      {inv.get('id')}")
        print(f"  Number:  {inv.get('invoice_number') or inv.get('number')}")
        print(f"  Status:  {inv.get('status')}")
        print(f"  Amount:  ${inv.get('grand_total') or inv.get('amount')}")
        print(f"  Date:    {inv.get('billing_date') or inv.get('invoice_date')}")
        print(f"  → PROCORE_INVOICE_ID={inv.get('id')}")


if __name__ == "__main__":
    get_invoices()
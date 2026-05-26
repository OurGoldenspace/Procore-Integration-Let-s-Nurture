
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

def get_invoices():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Procore-Company-Id": str(COMPANY_ID)
    }
    
    # Try owner invoices first
    response = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}/invoices",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    
    print(f"Owner Invoices Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Invoices found: {len(data)}")
        for inv in data:
            print(f"  Number: {inv.get('number')}")
            print(f"  ID: {inv.get('id')}")
            print(f"  Status: {inv.get('status')}")
            print(f"  Amount: {inv.get('grand_total')}")
            print(f"  Add to .env: PROCORE_INVOICE_ID={inv.get('id')}")
            print()
    else:
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    get_invoices()
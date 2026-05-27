import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

# Define base URLs from .env
PROCORE_BASE = os.getenv("PROCORE_BASE_URL")
SAGE_BASE    = os.getenv("SAGE_BASE_URL")

def sync_invoice_procore_to_sage(company_id, project_id, invoice_id):
    """
    Core P1 function:
    Pulls approved invoice from Procore → creates in Sage 300
    This runs every time an invoice is approved in Procore
    """
    token = get_token()
    
    if not token:
        print("Auth failed — cannot proceed")
        return False
    
    # Procore-Company-Id header is mandatory on every call
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(company_id)
    }
    
    # Step 1 — Extract: Pull invoice from Procore
    print(f"\nStep 1 — Fetching invoice {invoice_id} from Procore...")
    procore_response = requests.get(
        f"{PROCORE_BASE}/rest/v1.0/projects/{project_id}/invoices/{invoice_id}",
        headers=headers,
        params={"company_id": company_id}
    )
    
    print(f"Procore response: {procore_response.status_code}")
    
    if procore_response.status_code != 200:
        print(f"Failed to fetch from Procore: {procore_response.status_code}")
        print(procore_response.text)
        return False
    
    invoice = procore_response.json()
    print(f"Got invoice: #{invoice.get('number')}")
    
    # Step 2 — Transform: Map Procore fields → Sage 300 fields
    # Fields confirmed by accounting team in meeting:
    # customer name, invoice number, pre-tax amount, tax
    print(f"\nStep 2 — Mapping fields to Sage 300 format...")
    sage_payload = {
        "customer_name":  invoice.get("contractor", {}).get("name"),
        "invoice_number": invoice.get("number"),
        "pre_tax_amount": invoice.get("subtotal"),
        "tax_amount":     invoice.get("tax_amount"),
        "total":          invoice.get("grand_total"),
        "job_number":     str(project_id),
        "date":           invoice.get("invoice_date"),
        "notes":          "Auto-synced from Procore on approval"
    }
    
    print(f"Mapped payload: {sage_payload}")
    
    # Step 3 — Load: Push to Sage 300
    print(f"\nStep 3 — Creating invoice in Sage 300...")
    sage_response = requests.post(
        f"{SAGE_BASE}/ar-invoices",
        json=sage_payload
    )
    
    print(f"Sage response: {sage_response.status_code}")
    
    if sage_response.status_code in [200, 201]:
        result = sage_response.json()
        print(f"\n✅ Success — Invoice created in Sage 300")
        print(f"   Sage ID:        {result.get('id')}")
        print(f"   Invoice Number: {result.get('invoice_number')}")
        print(f"   Status:         {result.get('status')}")
        return True
    else:
        print(f"\n❌ Failed to create in Sage: {sage_response.status_code}")
        print(sage_response.text)
        return False


if __name__ == "__main__":
    print("=== Procore → Sage 300 Integration (P1) ===\n")
    
    # Load IDs from .env
    COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
    PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")
    INVOICE_ID = os.getenv("PROCORE_INVOICE_ID")
    
    # Validate all IDs are present
    missing = []
    if not COMPANY_ID: missing.append("PROCORE_COMPANY_ID")
    if not PROJECT_ID: missing.append("PROCORE_PROJECT_ID")
    if not INVOICE_ID: missing.append("PROCORE_INVOICE_ID")
    
    if missing:
        print(f"❌ Missing .env values: {', '.join(missing)}")
        print("Run get_company_id.py, get_project_id.py, get_invoice_id.py first")
        exit()
    
    print(f"Company ID: {COMPANY_ID}")
    print(f"Project ID: {PROJECT_ID}")
    print(f"Invoice ID: {INVOICE_ID}")
    
    # Run the integration
    success = sync_invoice_procore_to_sage(
        company_id=COMPANY_ID,
        project_id=PROJECT_ID,
        invoice_id=INVOICE_ID
    )
    
    if success:
        print("\n✅ P1 Integration complete")
    else:
        print("\n❌ Integration failed — check errors above")
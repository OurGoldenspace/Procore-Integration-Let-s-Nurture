import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

if __name__ == "__main__":
    sync_invoice_procore_to_sage(
        company_id=os.getenv("PROCORE_COMPANY_ID"),
        project_id=os.getenv("PROCORE_PROJECT_ID"),
        invoice_id=os.getenv("PROCORE_INVOICE_ID")
    )
    
def sync_invoice_procore_to_sage(company_id, project_id, invoice_id):
    """
    Core P1 function:
    Pulls approved invoice from Procore → creates in Sage 300
    This runs every time an invoice is approved in Procore
    """
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1 — Pull invoice from Procore
    print(f"Fetching invoice {invoice_id} from Procore...")
    procore_response = requests.get(
        f"{PROCORE_BASE}/rest/v1.0/projects/{project_id}/invoices/{invoice_id}",
        headers=headers,
        params={"company_id": company_id}
    )
    
    if procore_response.status_code != 200:
        print(f"Failed to fetch from Procore: {procore_response.status_code}")
        return False
    
    invoice = procore_response.json()
    print(f"Got invoice: #{invoice.get('number')}")
    
    # Step 2 — Map Procore fields → Sage 300 fields
    # Based on what accounting confirmed in the meeting
    sage_payload = {
        "customer_name": invoice.get("contractor", {}).get("name"),
        "invoice_number": invoice.get("number"),
        "pre_tax_amount": invoice.get("subtotal"),
        "tax_amount": invoice.get("tax_amount"),
        "total": invoice.get("grand_total"),
        "job_number": str(project_id),
        "date": invoice.get("invoice_date"),
        "notes": f"Auto-synced from Procore on approval"
    }
    
    print(f"Mapped payload: {sage_payload}")
    
    # Step 3 — Push to Sage 300
    print("Creating invoice in Sage 300...")
    sage_response = requests.post(
        f"{SAGE_BASE}/ar-invoices",
        json=sage_payload
    )
    
    if sage_response.status_code in [200, 201]:
        result = sage_response.json()
        print(f"Success — Invoice created in Sage 300")
        print(f"Sage ID: {result.get('id')}")
        return True
    else:
        print(f"Failed to create in Sage: {sage_response.status_code}")
        print(sage_response.text)
        return False

if __name__ == "__main__":
    # Test with sandbox IDs — get from procore_test.py output
    sync_invoice_procore_to_sage(
        company_id="YOUR_COMPANY_ID",
        project_id="YOUR_PROJECT_ID",
        invoice_id="YOUR_INVOICE_ID"
    )
import requests
import os
import logging
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

# Base URLs
PROCORE_BASE = os.getenv("PROCORE_BASE_URL")
SAGE_BASE    = os.getenv("SAGE_BASE_URL")

# Logging
logging.basicConfig(
    filename="integration.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

def get_approved_invoices(company_id, project_id, token):
    """
    Step 1 — Extract
    Fetches all approved invoices from Procore project
    """
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(company_id)
    }
    
    response = requests.get(
        f"{PROCORE_BASE}/rest/v1.0/projects/{project_id}/invoices",
        headers=headers,
        params={
            "company_id":      company_id,
            "filters[status]": "approved"
        }
    )
    
    if response.status_code == 200:
        invoices = response.json()
        approved = [
            inv for inv in invoices
            if inv.get("status", "").lower() == "approved"
        ]
        print(f"✅ Found {len(approved)} approved invoices")
        logging.info(f"Found {len(approved)} approved invoices")
        return approved
    else:
        print(f"❌ Failed to fetch invoices: {response.status_code}")
        logging.error(f"Failed to fetch invoices: {response.text}")
        return []

def sync_invoice_procore_to_sage(company_id, project_id, invoice_id):
    """
    Core P1 function — ETL pipeline
    Extract from Procore → Transform fields → Load to Sage
    """
    token = get_token()
    if not token:
        print("❌ Auth failed")
        return False
    
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(company_id)
    }
    
    # EXTRACT — pull invoice from Procore
    print(f"\nExtracting invoice {invoice_id} from Procore...")
    procore_response = requests.get(
        f"{PROCORE_BASE}/rest/v1.0/projects/{project_id}/invoices/{invoice_id}",
        headers=headers,
        params={"company_id": company_id}
    )
    
    if procore_response.status_code != 200:
        print(f"❌ Procore fetch failed: {procore_response.status_code}")
        logging.error(f"Procore fetch failed: {procore_response.text}")
        return False
    
    invoice = procore_response.json()
    print(f"✅ Got invoice: #{invoice.get('number')}")
    
    # TRANSFORM — map Procore fields to Sage 300
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
    
    # Validate required fields
    missing = [k for k, v in sage_payload.items() if not v]
    if missing:
        print(f"❌ Missing fields: {missing}")
        logging.error(f"Missing fields for invoice {invoice_id}: {missing}")
        return False
    
    print(f"✅ Fields mapped: {sage_payload}")
    
    # LOAD — push to Sage via hh2 or CSV fallback
    return load_to_sage(sage_payload, company_id)

def load_to_sage(sage_payload, company_id):
    """
    LOAD step — tries hh2 first, falls back to CSV
    Automatically switches based on what's configured
    """
    HH2_BASE_URL = os.getenv("HH2_BASE_URL")
    HH2_API_KEY  = os.getenv("HH2_API_KEY")
    
    # Try hh2 if configured
    if HH2_BASE_URL and HH2_API_KEY:
        print("Loading via hh2...")
        return sync_via_hh2(sage_payload, HH2_BASE_URL, HH2_API_KEY)
    
    # Try Sage mock / real Sage API
    if SAGE_BASE:
        print("Loading via Sage API / mock...")
        response = requests.post(
            f"{SAGE_BASE}/ar-invoices",
            json=sage_payload
        )
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Invoice created in Sage 300")
            print(f"   Sage ID: {result.get('id')}")
            logging.info(f"Invoice synced: {sage_payload['invoice_number']}")
            return True
        else:
            print(f"❌ Sage API failed: {response.status_code}")
    
    # CSV fallback — always works
    print("Loading via CSV fallback...")
    from csv_integration import procore_to_sage_csv
    filepath = procore_to_sage_csv(sage_payload)
    if filepath:
        print(f"✅ CSV generated: {filepath}")
        logging.info(f"CSV fallback used: {filepath}")
        return True
    
    return False

def sync_via_hh2(sage_payload, base_url, api_key):
    """Load via hh2 middleware — populated after discovery call"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json"
    }
    response = requests.post(
        f"{base_url}/ar-invoices",
        headers=headers,
        json=sage_payload
    )
    if response.status_code in [200, 201]:
        print(f"✅ Synced via hh2")
        logging.info(f"hh2 sync successful: {sage_payload['invoice_number']}")
        return True
    else:
        print(f"❌ hh2 failed: {response.status_code} — falling back to CSV")
        from csv_integration import procore_to_sage_csv
        return procore_to_sage_csv(sage_payload) is not None

if __name__ == "__main__":
    print("=== Procore → Sage 300 Integration (P1) ===\n")
    
    COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
    PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")
    
    if not COMPANY_ID or not PROJECT_ID:
        print("❌ Missing PROCORE_COMPANY_ID or PROJECT_ID in .env")
        exit()
    
    token = get_token()
    if not token:
        print("❌ Auth failed — check credentials")
        exit()
    
    # Get all approved invoices
    approved = get_approved_invoices(COMPANY_ID, PROJECT_ID, token)
    
    if not approved:
        print("No approved invoices to sync")
        exit()
    
    # Sync each one
    print(f"\nSyncing {len(approved)} invoices...\n")
    results = {"success": 0, "failed": 0}
    
    for invoice in approved:
        success = sync_invoice_procore_to_sage(
            company_id=COMPANY_ID,
            project_id=PROJECT_ID,
            invoice_id=invoice.get("id")
        )
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
    
    print(f"\n=== Sync Complete ===")
    print(f"✅ Successful: {results['success']}")
    print(f"❌ Failed:     {results['failed']}")
    print(f"Total:         {len(approved)}")
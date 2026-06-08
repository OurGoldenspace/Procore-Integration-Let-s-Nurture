# save as integration.py — full updated version
import requests
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
SAGE_BASE  = os.getenv("SAGE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%Y-%m-%d')}_integration.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

def build_headers(token):
    return {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(COMPANY_ID)
    }

def safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("$", ""))
    except:
        return 0.0

def convert_job_number(procore_job):
    """25-1355 → 25-1355-0"""
    if not procore_job:
        return ""
    cleaned = str(procore_job).rstrip("-0").rstrip("-")
    return f"{cleaned}-0"

def convert_cost_code(procore_code):
    """01-5204 → 01-520400"""
    if not procore_code:
        return ""
    parts = str(procore_code).split("-")
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}00"
    return procore_code

def format_sage_date(date_str):
    """YYYY-MM-DD → MM-DD-YYYY"""
    if not date_str:
        return ""
    try:
        if len(str(date_str)) >= 10:
            parts = str(date_str)[:10].split("-")
            if len(parts) == 3:
                return f"{parts[1]}-{parts[2]}-{parts[0]}"
    except:
        pass
    return str(date_str)

# ============================================
# FETCH FUNCTIONS
# ============================================

def get_owner_invoices(token):
    """Fetch approved owner invoices from payment_applications"""
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/payment_applications",
        headers=build_headers(token),
        params={
            "company_id": COMPANY_ID,
            "project_id": PROJECT_ID
        }
    )
    if r.status_code == 200:
        invoices = r.json()
        approved = [i for i in invoices 
                   if str(i.get("status","")).lower() == "approved"]
        print(f"✅ Owner invoices found: {len(approved)}")
        return approved
    print(f"❌ Owner invoices: {r.status_code}")
    return []

def get_subcontractor_invoices(token):
    """Fetch approved subcontractor invoices from requisitions"""
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/requisitions",
        headers=build_headers(token),
        params={
            "company_id": COMPANY_ID,
            "project_id": PROJECT_ID
        }
    )
    if r.status_code == 200:
        invoices = r.json()
        approved = [i for i in invoices 
                   if str(i.get("status","")).lower() == "approved"]
        print(f"✅ Subcontractor invoices found: {len(approved)}")
        return approved
    print(f"❌ Subcontractor invoices: {r.status_code}")
    return []

# ============================================
# TRANSFORM FUNCTIONS
# ============================================

def transform_owner_invoice(invoice):
    """
    Map owner invoice (payment_application) → Sage 300 AP fields
    Confirmed from real AGCM invoice data
    """
    g702 = invoice.get("g702", {})
    
    # Get cost code from first g703 line item
    g703 = invoice.get("g703", [])
    cost_code_raw = ""
    if g703:
        first_line = g703[0]
        cost_code_raw = first_line.get("cost_code", {}).get("full_code", "")
    
    pre_tax = safe_float(
        g702.get("total_completed_and_stored_to_date", 0)
    )
    tax = safe_float(
        g702.get("tax_applicable_to_this_payment", 0)
    )
    
    return {
        "invoice_type":   "owner",
        "vendor_code":    "",  # Quest Capital → lookup vendor code
        "invoice_number": invoice.get("invoice_number", ""),
        "invoice_date":   format_sage_date(invoice.get("billing_date", "")),
        "period_start":   format_sage_date(invoice.get("period_start", "")),
        "period_end":     format_sage_date(invoice.get("period_end", "")),
        "pre_tax_amount": pre_tax,
        "tax_amount":     tax,
        "total":          pre_tax + tax,
        "description":    f"#{PROJECT_ID} {invoice.get('formatted_contract_company', '')}",
        "job_number":     convert_job_number(
                              str(PROJECT_ID)
                          ),
        "cost_code":      convert_cost_code(cost_code_raw),
        "payment_type":   "Electronic",
        "tax_group":      "S1152",
        "procore_id":     invoice.get("id"),
        "contract_id":    invoice.get("contract", {}).get("id")
    }

def transform_subcontractor_invoice(invoice):
    """
    Map subcontractor invoice (requisition) → Sage 300 AP fields
    Confirmed from real AGCM invoice data
    """
    summary = invoice.get("summary", {})
    
    pre_tax = safe_float(
        summary.get("current_payment_due", 0)
    )
    tax = safe_float(
        summary.get("tax_applicable_to_this_payment", 0)
    )
    
    return {
        "invoice_type":   "subcontractor",
        "vendor_code":    "",  # vendor_name → lookup vendor code in Sage
        "vendor_name":    invoice.get("vendor_name", ""),
        "invoice_number": invoice.get("invoice_number", ""),
        "invoice_date":   format_sage_date(invoice.get("billing_date", "")),
        "period_start":   format_sage_date(invoice.get("requisition_start", "")),
        "period_end":     format_sage_date(invoice.get("requisition_end", "")),
        "pre_tax_amount": pre_tax,
        "tax_amount":     tax,
        "total":          pre_tax + tax,
        "description":    f"#{PROJECT_ID} {invoice.get('vendor_name', '')}",
        "job_number":     convert_job_number(str(PROJECT_ID)),
        "payment_type":   "Electronic",
        "tax_group":      "S1152",
        "procore_id":     invoice.get("id"),
        "commitment_id":  invoice.get("commitment_id")
    }

# ============================================
# LOAD FUNCTION
# ============================================

def load_to_sage(sage_payload):
    """
    Load invoice to Sage 300
    Tries: hh2 → Sage API → CSV fallback
    """
    HH2_URL = os.getenv("HH2_BASE_URL")
    HH2_KEY = os.getenv("HH2_API_KEY")
    
    # Path 1 — hh2
    if HH2_URL and HH2_KEY:
        r = requests.post(
            f"{HH2_URL}/ar-invoices",
            headers={"Authorization": f"Bearer {HH2_KEY}",
                     "Content-Type": "application/json"},
            json=sage_payload
        )
        if r.status_code in [200, 201]:
            print(f"✅ Synced via hh2")
            logging.info(f"hh2 sync: {sage_payload['invoice_number']}")
            return True
    
    # Path 2 — Sage API / mock
    if SAGE_BASE:
        r = requests.post(
            f"{SAGE_BASE}/ar-invoices",
            json=sage_payload
        )
        if r.status_code in [200, 201]:
            result = r.json()
            print(f"✅ Created in Sage 300")
            print(f"   Sage ID: {result.get('id')}")
            logging.info(f"Sage sync: {sage_payload['invoice_number']}")
            return True
    
    # Path 3 — CSV fallback
    from csv_integration import procore_to_sage_csv
    filepath = procore_to_sage_csv(sage_payload)
    if filepath:
        print(f"✅ CSV generated: {filepath}")
        logging.info(f"CSV: {filepath}")
        return True
    
    return False

# ============================================
# MAIN SYNC FUNCTION
# ============================================

def sync_all_approved_invoices():
    """
    Main P1 function — syncs all approved invoices
    Handles both owner and subcontractor invoices
    """
    print("=== Procore → Sage 300 Integration (P1) ===\n")
    
    token = get_token()
    if not token:
        print("❌ Auth failed")
        return
    
    results = {"success": 0, "failed": 0}
    
    # Process owner invoices
    print("[1/2] Processing owner invoices...")
    owner_invoices = get_owner_invoices(token)
    
    for inv in owner_invoices:
        print(f"\n  Invoice: #{inv.get('invoice_number')} "
              f"| {inv.get('formatted_contract_company')} "
              f"| ${inv.get('total_amount_accrued_this_period')}")
        
        sage_payload = transform_owner_invoice(inv)
        print(f"  Transformed: {sage_payload}")
        
        success = load_to_sage(sage_payload)
        results["success" if success else "failed"] += 1
    
    # Process subcontractor invoices
    print("\n[2/2] Processing subcontractor invoices...")
    sub_invoices = get_subcontractor_invoices(token)
    
    for inv in sub_invoices:
        summary = inv.get("summary", {})
        print(f"\n  Invoice: #{inv.get('invoice_number')} "
              f"| {inv.get('vendor_name')} "
              f"| ${summary.get('current_payment_due')}")
        
        sage_payload = transform_subcontractor_invoice(inv)
        print(f"  Transformed: {sage_payload}")
        
        success = load_to_sage(sage_payload)
        results["success" if success else "failed"] += 1
    
    # Summary
    total = results["success"] + results["failed"]
    print(f"\n=== Sync Complete ===")
    print(f"✅ Success: {results['success']}/{total}")
    print(f"❌ Failed:  {results['failed']}/{total}")
    
    if results["failed"] == 0:
        print("\n✅ P1 Integration complete — all invoices synced")
    
    return results

if __name__ == "__main__":
    sync_all_approved_invoices()
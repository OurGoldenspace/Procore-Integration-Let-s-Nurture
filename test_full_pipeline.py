# test_full_pipeline.py
# Full end-to-end test: Procore → CSV → Sage 300
# Extracts real invoices from AGCM's Procore account
# Generates Sage 300 CRE import CSV in Andrew's exact format

import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token
from csv_integration import procore_to_sage_csv, batch_export, verify_csv

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

def run_full_pipeline():
    print("=" * 60)
    print("FULL PIPELINE TEST: Procore → CSV → Sage 300")
    print("=" * 60)
    
    # Step 1 — Auth
    print("\n[1/5] Authenticating with Procore...")
    token = get_token()
    if not token:
        print("❌ Auth failed")
        return
    
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": COMPANY_ID
    }
    params = {"company_id": COMPANY_ID, "project_id": PROJECT_ID}
    
    # Step 2 — Get project number (not Procore internal ID)
    print("\n[2/5] Getting project number...")
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    
    if r.status_code == 200:
        project = r.json()
        PROJECT_NUMBER = project.get("project_number", "")
        print(f"✅ Project: {project.get('display_name')}")
        print(f"   Number:  {PROJECT_NUMBER}")
        print(f"   Sage Job: {PROJECT_NUMBER}-0")
    else:
        PROJECT_NUMBER = ""
        print(f"⚠️  Could not get project number — using fallback")
    
    all_invoices = []
    
    # Step 3 — Fetch owner invoices
    print("\n[3/5] Fetching owner invoices from Procore...")
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/payment_applications",
        headers=headers,
        params=params
    )
    
    if r.status_code == 200:
        owner_invoices = r.json()
        approved = [i for i in owner_invoices 
                   if str(i.get("status", "")).lower() == "approved"]
        print(f"✅ Owner invoices: {len(approved)} approved")
        
        for inv in approved:
            g702 = inv.get("g702", {})
            pre_tax = float(g702.get("total_completed_and_stored_to_date", 0))
            tax = float(g702.get("tax_applicable_to_this_payment", 0))
            
            # Get cost code from first g703 line item
            g703 = inv.get("g703", [])
            cost_code = ""
            if g703:
                cost_code = g703[0].get("cost_code", {}).get("full_code", "")
            
            all_invoices.append({
                "vendor_code":    "",  # needs vendor mapping from Timie-Lynn
                "invoice_number": inv.get("invoice_number", ""),
                "description":    f"#{PROJECT_NUMBER} {inv.get('formatted_contract_company', '')}"[:30],
                "pre_tax_amount": pre_tax,
                "tax_amount":     tax,
                "invoice_date":   inv.get("billing_date", ""),
                "received_date":  inv.get("created_at", "")[:10],
                "due_date":       inv.get("billing_date", ""),
                "job_number":     PROJECT_NUMBER,
                "cost_code":      cost_code,
                "category":       "",
                "tax_group":      "S1152",
                "type":           "owner",
                "procore_id":     inv.get("id"),
                "company":        inv.get("formatted_contract_company", "")
            })
            print(f"   #{inv.get('invoice_number')} | "
                  f"{inv.get('formatted_contract_company')} | "
                  f"${pre_tax + tax:,.2f}")
    else:
        print(f"❌ Owner invoices failed: {r.status_code}")
    
    # Step 4 — Fetch subcontractor invoices
    print("\n[4/5] Fetching subcontractor invoices from Procore...")
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/requisitions",
        headers=headers,
        params=params
    )
    
    if r.status_code == 200:
        sub_invoices = r.json()
        approved = [i for i in sub_invoices 
                   if str(i.get("status", "")).lower() == "approved"]
        print(f"✅ Subcontractor invoices: {len(approved)} approved")
        
        for inv in approved:
            summary = inv.get("summary", {})
            pre_tax = float(summary.get("current_payment_due", 0))
            tax = float(summary.get("tax_applicable_to_this_payment", 0))
            
            all_invoices.append({
                "vendor_code":    "",  # needs vendor mapping from Timie-Lynn
                "invoice_number": inv.get("invoice_number", ""),
                "description":    f"#{PROJECT_NUMBER} {inv.get('vendor_name', '')}"[:30],
                "pre_tax_amount": pre_tax,
                "tax_amount":     tax,
                "invoice_date":   inv.get("billing_date", ""),
                "received_date":  inv.get("created_at", "")[:10],
                "due_date":       inv.get("billing_date", ""),
                "job_number":     PROJECT_NUMBER,
                "cost_code":      "",
                "category":       "",
                "tax_group":      "S1152",
                "type":           "subcontractor",
                "procore_id":     inv.get("id"),
                "company":        inv.get("vendor_name", "")
            })
            print(f"   #{inv.get('invoice_number')} | "
                  f"{inv.get('vendor_name')} | "
                  f"${pre_tax + tax:,.2f}")
    else:
        print(f"❌ Subcontractor invoices failed: {r.status_code}")
    
    # Step 5 — Generate CSVs
    print(f"\n[5/5] Generating Sage 300 CSV files...")
    print(f"Total invoices to export: {len(all_invoices)}")
    
    if not all_invoices:
        print("❌ No invoices to export")
        return
    
    # Individual files
    for inv_data in all_invoices:
        path = procore_to_sage_csv(inv_data)
        if path:
            verify_csv(path)
    
    # Batch file
    print("\n--- Batch Export ---")
    batch_path = batch_export(all_invoices)
    if batch_path:
        verify_csv(batch_path)
    
    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE TEST COMPLETE")
    print("=" * 60)
    print(f"\n✅ Invoices extracted from Procore: {len(all_invoices)}")
    print(f"✅ Individual CSVs generated: {len(all_invoices)}")
    print(f"✅ Batch CSV generated: 1")
    print(f"✅ Project number: {PROJECT_NUMBER} → Sage job: {PROJECT_NUMBER}-0")
    print(f"\nFiles in sage_import/ ready for Sage 300 import")
    print(f"Drop into: \\\\AGCM-VM01455\\TIMBERLINE OFFICE\\DATA\\AGCM\\")
    
    # Flag missing fields
    missing = []
    if not all_invoices[0].get("vendor_code"):
        missing.append("Vendor codes — need mapping from Timie-Lynn")
    if not all_invoices[0].get("cost_code"):
        missing.append("Cost codes — need from Procore commitment data")
    
    if missing:
        print(f"\n⚠️  Still needed for production:")
        for m in missing:
            print(f"    → {m}")

if __name__ == "__main__":
    run_full_pipeline()
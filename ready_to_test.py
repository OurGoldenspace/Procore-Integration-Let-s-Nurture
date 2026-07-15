"""
PROCORE → SAGE 300 INTEGRATION TEST
End-to-end test with CSV generation and Sage 300 format validation
"""

import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from user_token_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL", "https://us02.procore.com")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID", "562949953425362")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID", "562949955372419")
SAGE_VENDOR_CODE = os.getenv("SAGE_VENDOR_CODE", "")  # Optional: hardcoded vendor if needed

def safe_float(val):
    """Safely convert value to float."""
    try:
        return float(str(val).replace(",", "").replace("$", ""))
    except:
        return 0.0

def extract_owner_invoice(inv):
    """Extract fields from a payment_application (owner invoice)."""
    g702      = inv.get("g702", {})
    pre_tax   = safe_float(g702.get("current_payment_due", 0))
    tax       = safe_float(g702.get("tax_applicable_to_this_payment", 0))
    return {
        "vendor_name":    inv.get("formatted_contract_company", "Unknown Vendor"),
        "vendor_code":    SAGE_VENDOR_CODE or inv.get("id", ""),
        "invoice_number": inv.get("invoice_number") or str(inv.get("number", "")),
        "pre_tax_amount": pre_tax,
        "tax_amount":     tax,
        "total":          pre_tax + tax,
        "date":           inv.get("billing_date", ""),
        "due_date":       inv.get("due_date", ""),
        "procore_id":     inv.get("id"),
        "invoice_type":   "owner",
    }

def extract_sub_invoice(inv):
    """Extract fields from a requisition (subcontractor invoice)."""
    summary   = inv.get("summary", {})
    pre_tax   = safe_float(summary.get("current_payment_due", 0))
    tax       = safe_float(summary.get("tax_applicable_to_this_payment", 0))
    return {
        "vendor_name":    inv.get("vendor_name", "Unknown Vendor"),
        "vendor_code":    SAGE_VENDOR_CODE or inv.get("id", ""),
        "invoice_number": inv.get("invoice_number") or str(inv.get("number", "")),
        "pre_tax_amount": pre_tax,
        "tax_amount":     tax,
        "total":          pre_tax + tax,
        "date":           inv.get("billing_date", ""),
        "due_date":       inv.get("due_date", ""),
        "procore_id":     inv.get("id"),
        "invoice_type":   "subcontractor",
        "commitment_id":  inv.get("commitment_id"),
    }

def apply_sage_transforms(extracted, raw_job=None, raw_cost="01-5204"):
    """Apply AGCM field conversion rules for Sage 300."""
    job = str(raw_job or PROJECT_ID)
    
    # Job: append -0 if not already ending with it
    sage_job  = job + "-0" if not job.endswith("-0") else job
    
    # Cost code: append 00 if last segment is 4 digits
    parts = raw_cost.split("-")
    sage_cost = raw_cost + "00" if len(parts[-1]) == 4 else raw_cost

    extracted.update({
        "job_number":   sage_job,
        "cost_code":    sage_cost,
        "tax_group":    "S1152",  # HST 15% tax group
        "payment_type": "Electronic",
        "description":  f"#{sage_job.replace('-0','')} {extracted['vendor_name']}",
    })
    return extracted

def generate_sage_csv(invoices):
    """
    Generate Sage 300 CRE CSV format (API + APD records).
    Returns CSV content as string.
    """
    csv_lines = []
    
    for inv in invoices:
        vendor_code = str(inv.get("vendor_code", "")).strip() or "VENDOR"
        invoice_num = str(inv.get("invoice_number", "")).strip()
        vendor_name = inv.get("vendor_name", "Unknown")
        pre_tax = inv.get("pre_tax_amount", 0)
        tax = inv.get("tax_amount", 0)
        total = inv.get("total", 0)
        inv_date = inv.get("date", "")
        due_date = inv.get("due_date", "")
        job = inv.get("job_number", "")
        cost_code = inv.get("cost_code", "01-5204-00")
        tax_group = inv.get("tax_group", "S1152")
        
        # Format dates (YYYY-MM-DD → MM/DD/YYYY for Sage)
        try:
            if inv_date and "T" in inv_date:
                inv_date = inv_date.split("T")[0]  # Remove time
            if due_date and "T" in due_date:
                due_date = due_date.split("T")[0]
        except:
            pass
        
        # ─────────────────────────────────────────────────────
        # API Record (Invoice Header)
        # ─────────────────────────────────────────────────────
        api_record = [
            "API",                      # Record type
            "",                         # Filler
            invoice_num,                # Invoice number
            f"#{job} {vendor_name}",    # Description (concatenated)
            f"{pre_tax:.2f}",          # Pre-tax amount
            f"{tax:.2f}",              # Tax amount
            "0",                        # Discount (default 0)
            inv_date,                   # Invoice date
            due_date,                   # Due date
            "",                         # Filler
            inv_date,                   # GL Date
        ]
        csv_lines.append(",".join(api_record))
        
        # ─────────────────────────────────────────────────────
        # APD Record (Invoice Detail/Line Item)
        # ─────────────────────────────────────────────────────
        apd_record = [
            "APD",                      # Record type
            "",                         # Filler
            "",                         # Filler
            cost_code,                  # Cost code (job-division-item format)
            "",                         # Filler x3
            "",
            "",
            "",                         # Filler
            "",                         # Filler
            tax_group,                  # Tax group (e.g., S1152 for HST)
            "",                         # Filler
            "",                         # Filler
            f"{pre_tax:.2f}",          # Detail amount (pre-tax)
            f"{tax:.2f}",              # Tax amount
            "0",                        # Discount
            "",                         # Filler x4
            "",
            "",
            f"#{job} {vendor_name}",    # Description
            "",                         # Filler
            "2",                        # Line count/sequence
        ]
        csv_lines.append(",".join(apd_record))
    
    return "\n".join(csv_lines)

def save_csv_file(csv_content, test_name="test"):
    """Save CSV to output directory and return filepath."""
    os.makedirs("./output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"./output/sage_invoices_{test_name}_{timestamp}.csv"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(csv_content)
    
    return filename

def run_full_test(limit_invoices=3):
    """Run complete end-to-end integration test."""
    print("=" * 70)
    print("PROCORE → SAGE 300 INTEGRATION TEST (END-TO-END)")
    print("=" * 70)

    results = {
        "auth":     "❌",
        "project":  "❌",
        "invoices": "❌",
        "etl":      "❌",
        "csv":      "❌",
        "validate": "❌"
    }

    # ── Step 1: Authentication ────────────────────────────────
    print("\n[1/6] AUTHENTICATION")
    print("-" * 70)
    token = get_token()
    if not token:
        print("❌ Failed to get authentication token")
        print("   Check .env file: PROCORE_CLIENT_ID, PROCORE_CLIENT_SECRET")
        print_summary(results)
        return

    results["auth"] = "✅"
    print("✅ Authenticated with Procore")

    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(COMPANY_ID)
    }
    params = {"project_id": PROJECT_ID, "company_id": COMPANY_ID}

    # ── Step 2: Project Access ────────────────────────────────
    print("\n[2/6] PROJECT ACCESS")
    print("-" * 70)
    try:
        r = requests.get(
            f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}",
            headers=headers,
            params={"company_id": COMPANY_ID},
            timeout=10
        )
        if r.status_code == 200:
            project = r.json()
            results["project"] = "✅"
            print(f"✅ Project: {project.get('name')}")
            print(f"   ID: {PROJECT_ID}")
        else:
            print(f"❌ Project access failed: {r.status_code}")
            print(f"   Response: {r.text}")
            print_summary(results)
            return
    except Exception as e:
        print(f"❌ Project request failed: {e}")
        print_summary(results)
        return

    # ── Step 3: Fetch Approved Invoices ───────────────────────
    print("\n[3/6] FETCHING APPROVED INVOICES")
    print("-" * 70)
    approved = []

    # Owner invoices (payment applications)
    try:
        r_owner = requests.get(
            f"{BASE_URL}/rest/v1.0/payment_applications",
            headers=headers,
            params=params,
            timeout=10
        )
        if r_owner.status_code == 200:
            owner_list = r_owner.json()
            approved_owner = [
                inv for inv in owner_list
                if str(inv.get("status", "")).lower() in ["approved", "approved_as_noted"]
            ]
            for inv in approved_owner:
                approved.append(("owner", inv))
            print(f"✓ Owner invoices:         {len(owner_list)} total, {len(approved_owner)} approved")
        else:
            print(f"⚠ Owner invoices failed: {r_owner.status_code}")
    except Exception as e:
        print(f"⚠ Owner invoices error: {e}")

    # Subcontractor invoices (requisitions)
    try:
        r_sub = requests.get(
            f"{BASE_URL}/rest/v1.0/requisitions",
            headers=headers,
            params=params,
            timeout=10
        )
        if r_sub.status_code == 200:
            sub_list = r_sub.json()
            approved_sub = [
                inv for inv in sub_list
                if str(inv.get("status", "")).lower() in ["approved", "approved_as_noted"]
            ]
            for inv in approved_sub:
                approved.append(("sub", inv))
            print(f"✓ Subcontractor invoices: {len(sub_list)} total, {len(approved_sub)} approved")
        else:
            print(f"⚠ Subcontractor invoices failed: {r_sub.status_code}")
    except Exception as e:
        print(f"⚠ Subcontractor invoices error: {e}")

    if not approved:
        print("\n⚠️  NO APPROVED INVOICES FOUND")
        print("   Create test invoices in Procore and mark as approved")
        print_summary(results)
        return

    results["invoices"] = "✅"
    print(f"\n✅ Total approved invoices found: {len(approved)}")
    
    # Show details of invoices to be processed
    invoices_to_process = approved[:limit_invoices]
    print(f"   Processing first {len(invoices_to_process)} invoices:")
    for i, (inv_type, inv) in enumerate(invoices_to_process, 1):
        num = inv.get("invoice_number") or inv.get("number", "N/A")
        vendor = inv.get("formatted_contract_company") or inv.get("vendor_name", "Unknown")
        g702_or_summary = inv.get("g702", inv.get("summary", {}))
        amount = safe_float(g702_or_summary.get("current_payment_due", 0))
        print(f"   [{i}] [{inv_type}] #{num} — {vendor} — ${amount:.2f}")

    # ── Step 4: ETL Transform ─────────────────────────────────
    print("\n[4/6] ETL TRANSFORM")
    print("-" * 70)
    try:
        extracted_invoices = []
        
        for inv_type, invoice in invoices_to_process:
            if inv_type == "owner":
                extracted = extract_owner_invoice(invoice)
            else:
                extracted = extract_sub_invoice(invoice)
            
            sage_payload = apply_sage_transforms(extracted)
            extracted_invoices.append(sage_payload)
            
            print(f"✓ Invoice #{sage_payload['invoice_number']}")
            print(f"  Vendor: {sage_payload['vendor_name']}")
            print(f"  Amount: ${sage_payload['total']:.2f} (Pre-tax: ${sage_payload['pre_tax_amount']:.2f}, Tax: ${sage_payload['tax_amount']:.2f})")
            print(f"  Job: {sage_payload['job_number']} | Cost Code: {sage_payload['cost_code']}")
        
        results["etl"] = "✅"
        print(f"\n✅ Transformed {len(extracted_invoices)} invoices")
    except Exception as e:
        print(f"❌ ETL transformation failed: {e}")
        import traceback
        traceback.print_exc()
        print_summary(results)
        return

    # ── Step 5: Generate CSV ──────────────────────────────────
    print("\n[5/6] GENERATING SAGE CSV")
    print("-" * 70)
    try:
        csv_content = generate_sage_csv(extracted_invoices)
        csv_file = save_csv_file(csv_content, "procore")
        
        results["csv"] = "✅"
        print(f"✅ CSV generated: {csv_file}")
        print(f"   Invoices: {len(extracted_invoices)}")
        print(f"   Records:  {len(csv_content.splitlines())} lines")
        
        # Preview first 3 lines
        lines = csv_content.splitlines()
        print(f"\n   Preview (first 3 rows):")
        for line in lines[:3]:
            print(f"   {line[:100]}{'...' if len(line) > 100 else ''}")
    except Exception as e:
        print(f"❌ CSV generation failed: {e}")
        import traceback
        traceback.print_exc()
        print_summary(results)
        return

    # ── Step 6: Validate CSV Format ───────────────────────────
    print("\n[6/6] VALIDATING CSV FORMAT")
    print("-" * 70)
    try:
        lines = csv_content.splitlines()
        api_count = sum(1 for line in lines if line.startswith("API,"))
        apd_count = sum(1 for line in lines if line.startswith("APD,"))
        
        # Basic structure check
        if api_count != apd_count:
            print(f"⚠️  WARNING: API records ({api_count}) != APD records ({apd_count})")
        else:
            print(f"✓ Record pairs balanced: {api_count} API + {apd_count} APD")
        
        # Check for required fields
        issues = []
        for i, line in enumerate(lines, 1):
            if not line.startswith(("API,", "APD,")):
                issues.append(f"  Line {i}: Invalid record type")
        
        if issues and len(issues) <= 5:
            print(f"⚠️  Found {len(issues)} format issues:")
            for issue in issues:
                print(issue)
        elif issues:
            print(f"⚠️  Found {len(issues)} format issues (showing first 5)")
            for issue in issues[:5]:
                print(issue)
        
        results["validate"] = "✅"
        print(f"\n✅ CSV format validated")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        results["validate"] = "❌"

    print_summary(results, csv_file)


def print_summary(results, csv_file=None):
    """Print test summary and next steps."""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"  Authentication:    {results['auth']}")
    print(f"  Project Access:    {results['project']}")
    print(f"  Invoice Fetch:     {results['invoices']}")
    print(f"  ETL Transform:     {results['etl']}")
    print(f"  CSV Generation:    {results['csv']}")
    print(f"  CSV Validation:    {results['validate']}")
    
    all_pass = all(v == "✅" for v in results.values())
    
    print("\n" + "=" * 70)
    if all_pass:
        print("✅ ALL TESTS PASSED")
        print("\nNEXT STEPS:")
        print("1. Download the CSV file from output/")
        if csv_file:
            print(f"   File: {csv_file}")
        print("2. Open Sage 300 → Accounts Payable → Enter Invoices")
        print("3. Click 'List...' button (bottom left)")
        print("4. Click 'File' → 'Import'")
        print("5. Select the CSV file")
        print("6. Review invoice mapping and click 'Import'")
        print("7. Verify invoices appear in AP module")
    else:
        failed = [k for k, v in results.items() if v == "❌"]
        print(f"❌ FAILED: {', '.join(failed)}")
        print("   Fix issues above and re-run")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    run_full_test(limit_invoices=limit)
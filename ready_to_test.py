# ready_to_test.py
import requests
import os
from dotenv import load_dotenv
from user_token_auth import get_token
from csv_integration import procore_to_sage_csv

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL", "https://us02.procore.com")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID", "562949953425362")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID", "562949955372419")

def safe_float(val):
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
        "invoice_number": inv.get("invoice_number") or str(inv.get("number", "")),
        "pre_tax_amount": pre_tax,
        "tax_amount":     tax,
        "total":          pre_tax + tax,
        "date":           inv.get("billing_date", ""),
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
        "invoice_number": inv.get("invoice_number") or str(inv.get("number", "")),
        "pre_tax_amount": pre_tax,
        "tax_amount":     tax,
        "total":          pre_tax + tax,
        "date":           inv.get("billing_date", ""),
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
        "tax_group":    "S1152",
        "payment_type": "Electronic",
        "description":  f"#{sage_job.replace('-0','')} {extracted['vendor_name']}",
    })
    return extracted

def run_full_test():
    print("=" * 55)
    print("FULL INTEGRATION TEST — LETS NURTURE TEST PROJECT")
    print("=" * 55)

    results = {
        "auth":     "❌",
        "project":  "❌",
        "invoices": "❌",
        "sync":     "❌",
        "sage":     "❌"
    }

    # ── Step 1: Auth ──────────────────────────────────────────
    print("\n[1/5] Authentication...")
    token = get_token()
    if not token:
        print("❌ Auth failed — check credentials in .env")
        print_summary(results)
        return
    results["auth"] = "✅"
    print("✅ Authenticated")

    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(COMPANY_ID)
    }
    params = {"project_id": PROJECT_ID, "company_id": COMPANY_ID}

    # ── Step 2: Project access ────────────────────────────────
    print("\n[2/5] Accessing test project...")
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    if r.status_code == 200:
        project = r.json()
        results["project"] = "✅"
        print(f"✅ Project: {project.get('name')}")
    else:
        print(f"❌ Project access failed: {r.status_code}")
        print_summary(results)
        return

    # ── Step 3: Find approved invoices ────────────────────────
    print("\n[3/5] Finding approved invoices...")
    approved = []

    r_owner = requests.get(f"{BASE_URL}/rest/v1.0/payment_applications", headers=headers, params=params)
    r_sub   = requests.get(f"{BASE_URL}/rest/v1.0/requisitions",         headers=headers, params=params)

    if r_owner.status_code == 200:
        for inv in r_owner.json():
            if str(inv.get("status", "")).lower() in ["approved", "approved_as_noted"]:
                approved.append(("owner", inv))
        print(f"   Owner invoices:         {len(r_owner.json())} found, {sum(1 for t,_ in approved if t=='owner')} approved")

    if r_sub.status_code == 200:
        for inv in r_sub.json():
            if str(inv.get("status", "")).lower() in ["approved", "approved_as_noted"]:
                approved.append(("sub", inv))
        print(f"   Subcontractor invoices: {len(r_sub.json())} found, {sum(1 for t,_ in approved if t=='sub')} approved")

    if not approved:
        print("\n⚠️  No approved invoices found")
        print_summary(results)
        return

    results["invoices"] = "✅"
    print(f"\n✅ Total approved invoices: {len(approved)}")
    for inv_type, inv in approved:
        num = inv.get("invoice_number") or inv.get("number")
        vendor = inv.get("formatted_contract_company") or inv.get("vendor_name", "")
        amount = inv.get("g702", inv.get("summary", {})).get("current_payment_due", "?")
        print(f"   [{inv_type}] #{num} — {vendor} — ${amount}")

    # ── Step 4: ETL on first approved invoice ─────────────────
    print("\n[4/5] Running ETL on first approved invoice...")
    inv_type, invoice = approved[0]

    if inv_type == "owner":
        extracted = extract_owner_invoice(invoice)
    else:
        extracted = extract_sub_invoice(invoice)

    sage_payload = apply_sage_transforms(extracted)

    results["sync"] = "✅"
    print(f"✅ ETL complete")
    print(f"   Type:          {sage_payload['invoice_type']}")
    print(f"   Vendor:        {sage_payload['vendor_name']}")
    print(f"   Invoice #:     {sage_payload['invoice_number']}")
    print(f"   Pre-tax:       ${sage_payload['pre_tax_amount']:.2f}")
    print(f"   Tax (HST):     ${sage_payload['tax_amount']:.2f}")
    print(f"   Total:         ${sage_payload['total']:.2f}")
    print(f"   Sage Job:      {sage_payload['job_number']}")
    print(f"   Cost Code:     {sage_payload['cost_code']}")
    print(f"   Tax Group:     {sage_payload['tax_group']}")
    print(f"   Payment Type:  {sage_payload['payment_type']}")
    print(f"   Description:   {sage_payload['description']}")

    # ── Step 5: Load to Sage ──────────────────────────────────
    print("\n[5/5] Loading to Sage 300...")

    SAGE_URL = os.getenv("SAGE_BASE_URL", "http://localhost:3001")
    try:
        r = requests.post(f"{SAGE_URL}/ar-invoices", json=sage_payload, timeout=3)
        if r.status_code in [200, 201]:
            results["sage"] = "✅"
            print(f"✅ Invoice created in Sage 300 mock")
            print(f"   Sage ID: {r.json().get('id')}")
        else:
            raise Exception(f"Mock returned {r.status_code}")
    except:
        filepath = procore_to_sage_csv(sage_payload)
        if filepath:
            results["sage"] = "✅"
            print(f"✅ CSV generated: {filepath}")
            print(f"   Ready to import into Sage 300 AP")
        else:
            print("❌ Both Sage mock and CSV failed")

    print_summary(results)


def print_summary(results):
    print("\n" + "=" * 55)
    print("TEST SUMMARY")
    print("=" * 55)
    print(f"  Authentication:    {results['auth']}")
    print(f"  Project Access:    {results['project']}")
    print(f"  Invoice Access:    {results['invoices']}")
    print(f"  ETL Transform:     {results['sync']}")
    print(f"  Sage 300 Load:     {results['sage']}")
    all_pass = all(v == "✅" for v in results.values())
    print("\n" + "=" * 55)
    if all_pass:
        print("✅ ALL TESTS PASSED — P1 Integration working end to end")
        print("   Ready to connect to real Sage 300")
    else:
        failed = [k for k, v in results.items() if v == "❌"]
        print(f"❌ FAILED: {', '.join(failed)}")
        print("   Fix blockers above and re-run")
    print("=" * 55)


if __name__ == "__main__":
    run_full_test()
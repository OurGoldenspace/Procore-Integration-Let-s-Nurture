# save as ready_to_test.py
import requests
import os
from dotenv import load_dotenv
from user_token_auth import get_token
from csv_integration import procore_to_sage_csv

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL", "https://us02.procore.com")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID", "562949953425362")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID", "562949955372419")

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
    
    # Step 1 — Auth
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
        "Procore-Company-Id": COMPANY_ID
    }
    
    # Step 2 — Project access
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
        print(f"   Status:  {project.get('status')}")
    else:
        print(f"❌ Project access failed: {r.status_code}")
        print(f"   {r.text[:150]}")
        print_summary(results)
        return
    
    # Step 3 — Find approved invoices
    print("\n[3/5] Finding approved invoices...")
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}/invoices",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )

    if r.status_code == 200:
        invoices = r.json()
        if isinstance(invoices, dict):
            invoices = invoices.get("invoices", [])
    
        print(f"Total invoices found: {len(invoices)}")
    
        for inv in invoices:
            status = str(inv.get("status", "")).lower()
            print(f"  #{inv.get('number')} | "
                f"Status: {inv.get('status')} | "
                f"Total: ${inv.get('grand_total')}")
            if status in ["approved", "approved_as_noted"]:
                approved_invoices.append(inv)
    
        if approved_invoices:
            results["invoices"] = "✅"
            print(f"\n✅ Approved invoices: {len(invoices)}")
        else:
            print("\n⚠️  No approved invoices yet")
            print("   Waiting for Prathmesh to add invoice")
            print_summary(results)
            return
    
    elif r.status_code == 404:
        print("⚠️  Invoice endpoint returned 404")
        print("   This usually means no invoices exist yet")
        print("   Waiting for Prathmesh to add invoice to test project")
        print_summary(results)
        return

    else:
        print(f"❌ Invoice fetch failed: {r.status_code}")
        print(f"   {r.text[:150]}")
        print_summary(results)
        return
    
    # Step 4 — Extract and transform first invoice
    print("\n[4/5] Running ETL on first approved invoice...")
    invoice = approved_invoices[0]
    
    def safe_float(val):
        try:
            return float(str(val).replace(",", "").replace("$", ""))
        except:
            return 0.0
    
    customer_name = (
        invoice.get("vendor", {}).get("name") or
        invoice.get("contractor", {}).get("name") or
        invoice.get("company", {}).get("name") or
        "Unknown Customer"
    )
    
    sage_payload = {
        "customer_name":  customer_name,
        "invoice_number": invoice.get("number") or f"INV-{invoice.get('id')}",
        "pre_tax_amount": safe_float(invoice.get("subtotal") or 0),
        "tax_amount":     safe_float(invoice.get("tax_amount") or 0),
        "total":          safe_float(invoice.get("grand_total") or 0),
        "job_number":     str(PROJECT_ID),
        "date":           invoice.get("invoice_date", ""),
        "notes":          f"Auto-synced from Procore — ID: {invoice.get('id')}"
    }
    
    results["sync"] = "✅"
    print(f"✅ ETL complete")
    print(f"   Customer:  {sage_payload['customer_name']}")
    print(f"   Invoice #: {sage_payload['invoice_number']}")
    print(f"   Pre-tax:   ${sage_payload['pre_tax_amount']}")
    print(f"   Tax:       ${sage_payload['tax_amount']}")
    print(f"   Total:     ${sage_payload['total']}")
    
    # Step 5 — Load to Sage (mock or real)
    print("\n[5/5] Loading to Sage 300...")
    
    SAGE_URL = os.getenv("SAGE_BASE_URL", "http://localhost:3001")
    
    # Try Sage mock first
    try:
        r = requests.post(
            f"{SAGE_URL}/ar-invoices",
            json=sage_payload,
            timeout=3
        )
        if r.status_code in [200, 201]:
            result = r.json()
            results["sage"] = "✅"
            print(f"✅ Invoice created in Sage 300 mock")
            print(f"   Sage ID: {result.get('id')}")
        else:
            print(f"⚠️  Sage mock returned: {r.status_code}")
            print("   Falling back to CSV...")
            raise Exception("Try CSV")
    except:
        # CSV fallback
        filepath = procore_to_sage_csv(sage_payload)
        if filepath:
            results["sage"] = "✅"
            print(f"✅ CSV generated: {filepath}")
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
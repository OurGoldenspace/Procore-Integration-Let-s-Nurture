import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

def fresh_headers(company_id=None):
    """Get fresh token and headers for every test"""
    token = get_token()
    if not token:
        return None, None
    h = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }
    if company_id:
        h["Procore-Company-Id"] = str(company_id)
    return h, token

def run_diagnostics():
    print("=" * 50)
    print("PROCORE INTEGRATION DIAGNOSTICS")
    print("=" * 50)
    print(f"OAuth URL:  {os.getenv('PROCORE_OAUTH_URL')}")
    print(f"Base URL:   {BASE_URL}")
    print(f"Company ID: {COMPANY_ID}")
    print(f"Project ID: {PROJECT_ID}")
    
    # Test 1 — Auth
    print("\n[TEST 1] Authentication...")
    headers, token = fresh_headers()
    if not token:
        print("❌ FAILED — Check credentials in .env")
        return
    print("✅ PASSED")
    
    # Test 2 — Reachability
    print("\n[TEST 2] Procore reachability...")
    headers, token = fresh_headers()
    r = requests.get(f"{BASE_URL}/rest/v1.0/me", headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        me = r.json()
        print(f"✅ PASSED — Login: {me.get('login') or me.get('email')}")
    elif r.status_code == 401:
        print("❌ FAILED — 401 Token rejected by API")
        print(f"FIX: BASE_URL ({BASE_URL}) doesn't match your credentials")
        print("     Sandbox credentials need: https://sandbox.procore.com")
        print("     Production credentials need: https://us02.procore.com")
    else:
        print(f"❌ FAILED — {r.text[:150]}")
    
    # Test 3 — Company access
    print("\n[TEST 3] Company access...")
    headers, token = fresh_headers()
    r = requests.get(f"{BASE_URL}/rest/v1.0/companies", headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        companies = r.json()
        print(f"✅ PASSED — Companies: {len(companies)}")
        for c in companies:
            if isinstance(c, dict):
                print(f"   - {c.get('name')} | ID: {c.get('id')}")
    elif r.status_code == 403:
        print("❌ FAILED — 403 App owner restriction")
        print("FIX: Need AGCM's credentials from Prathmesh")
    else:
        print(f"❌ FAILED — {r.text[:150]}")
    
    # Test 4 — Project access
    print("\n[TEST 4] Test project access...")
    headers, token = fresh_headers(COMPANY_ID)
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        project = r.json()
        print(f"✅ PASSED — Project: {project.get('name')}")
    elif r.status_code == 401:
        print("❌ FAILED — 401 Token rejected")
        print(f"FIX: BASE_URL must match credential environment")
    elif r.status_code == 403:
        print("❌ FAILED — 403 No access")
        print("FIX: Need AGCM's production credentials")
    elif r.status_code == 404:
        print("❌ FAILED — 404 Project not found")
        print("FIX: Credentials from wrong environment")
        print("     Sandbox can't see us02.procore.com projects")
    else:
        print(f"❌ FAILED — {r.text[:150]}")
    
    # Test 5 — Invoices
    print("\n[TEST 5] Invoice access...")
    headers, token = fresh_headers(COMPANY_ID)
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}/invoices",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        invoices = r.json()
        if isinstance(invoices, list):
            print(f"✅ PASSED — Invoices: {len(invoices)}")
            for inv in invoices:
                print(f"   #{inv.get('number')} | {inv.get('status')} | ${inv.get('grand_total')}")
        else:
            print(f"✅ PASSED — {invoices}")
    elif r.status_code == 404:
        print("❌ FAILED — 404 No invoices or wrong environment")
        print("FIX 1: Ask Prathmesh to add dummy invoice to test project")
        print("FIX 2: Confirm credentials match project environment")
    else:
        print(f"❌ FAILED — {r.text[:150]}")
    
    # Test 6 — Sage mock
    print("\n[TEST 6] Sage 300 mock...")
    SAGE_URL = os.getenv("SAGE_BASE_URL", "http://localhost:3001")
    try:
        r = requests.get(f"{SAGE_URL}/health", timeout=3)
        if r.status_code == 200:
            print(f"✅ PASSED — Sage mock running")
        else:
            print(f"⚠️  Mock returned unexpected status: {r.status_code}")
    except Exception as e:
        print(f"❌ FAILED — Sage mock not running")
        print("FIX: Open Mockoon → click Play button")
    
    # Final summary
    print("\n" + "=" * 50)
    print("DIAGNOSIS COMPLETE")
    print("=" * 50)
    print("\nRoot cause of all failures:")
    print(f"  OAuth URL:  {os.getenv('PROCORE_OAUTH_URL')}")
    print(f"  Base URL:   {BASE_URL}")
    
    if "sandbox" in os.getenv('PROCORE_OAUTH_URL', '') and "us02" in BASE_URL:
        print("\n  ❌ MISMATCH DETECTED:")
        print("  Sandbox credentials + Production URL = will never work")
        print("\n  Fix options:")
        print("  Option A: Change BASE_URL to sandbox.procore.com")
        print("            (test with sandbox only)")
        print("  Option B: Get production credentials from Prathmesh")
        print("            (connect to real AGCM account)")
    elif "sandbox" in os.getenv('PROCORE_OAUTH_URL', '') and "sandbox" in BASE_URL:
        print("\n  ✅ Environment consistent — sandbox to sandbox")
        print("  If tests still fail, check credentials are correct")
    else:
        print("\n  ✅ Environment consistent — production to production")

if __name__ == "__main__":
    run_diagnostics()
# save as validate_env.py
import os
from dotenv import load_dotenv

load_dotenv()

def validate():
    print("=== Environment Validation ===\n")
    
    required = {
        "PROCORE_CLIENT_ID":     "Procore app Client ID",
        "PROCORE_CLIENT_SECRET": "Procore app Client Secret",
        "PROCORE_OAUTH_URL":     "OAuth token endpoint",
        "PROCORE_BASE_URL":      "Procore API base URL",
        "PROCORE_COMPANY_ID":    "AGCM Company ID",
        "PROCORE_PROJECT_ID":    "Test project ID"
    }
    
    optional = {
        "PROCORE_INVOICE_ID": "Test invoice ID",
        "SAGE_BASE_URL":      "Sage 300 URL or mock",
        "HH2_BASE_URL":       "hh2 middleware URL",
        "HH2_API_KEY":        "hh2 API key"
    }
    
    all_good = True
    
    print("Required:")
    for key, label in required.items():
        val = os.getenv(key)
        if val:
            masked = f"{val[:6]}...{val[-4:]}" if len(val) > 10 else val
            print(f"  ✅ {label}: {masked}")
        else:
            print(f"  ❌ {label}: NOT SET")
            all_good = False
    
    print("\nOptional:")
    for key, label in optional.items():
        val = os.getenv(key)
        status = f"{val[:6]}..." if val else "not set"
        icon = "✅" if val else "⚠️ "
        print(f"  {icon} {label}: {status}")
    
    print("\nEnvironment check:")
    base = os.getenv("PROCORE_BASE_URL", "")
    oauth = os.getenv("PROCORE_OAUTH_URL", "")
    
    if "sandbox" in base and "sandbox" in oauth:
        print("  ✅ Sandbox environment — testing mode")
    elif "us02" in base or "app.procore" in base:
        print("  ✅ Production environment — live mode")
    else:
        print("  ⚠️  Environment unclear — check URLs match")
    
    print(f"\n{'✅ Ready to test' if all_good else '❌ Fix missing values before testing'}")
    return all_good

if __name__ == "__main__":
    validate()